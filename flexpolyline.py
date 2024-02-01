# Copyright (C) 2019 HERE Europe B.V.
# Licensed under MIT
# SPDX-License-Identifier: MIT
# GitHub: https://github.com/heremaps/flexible-polyline

from typing import Optional
import numpy as np

FORMAT_VERSION = 1
ENCODING_TABLE = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
DECODING_TABLE = [
    62, -1, -1, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, -1, -1, -1, -1, -1, -1, -1,
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
    22, 23, 24, 25, -1, -1, -1, -1, 63, -1, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
    36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51
]

def encode(coordinates: np.array([], dtype=float), precision: int, is_list: Optional[bool] = False):
    if is_list:
        enc_output = np.array([], dtype=str)
        for point in coordinates:
            line = _encode(point, precision)
            enc_output = np.append(enc_output, line)
    
        return enc_output
    else:
        return _encode(coordinates, precision)

def decode(encoded, is_list: Optional[bool] = False, is_here: Optional[bool] = False):
    # encoded can be str or np.array([], dtype=str)
    if is_list:
        dec_output = np.empty((0, 2), dtype=float)
        for line in encoded:
            point = _decode(line, is_here)
            dec_output = np.append(dec_output, [point], axis=0)
        return dec_output
    else:
        return _decode(encoded, is_here)

def _encode(coordinates: np.array([], dtype=float), precision: int):
    # precision represents how many decimal digits of precision to store the latitude and longitude
    multiplier_degree = 10 ** precision

    last_lat = last_lng = 0

    res = np.array([], dtype=str)
    
    res = _encode_header(precision, res)

    lat = int(round(coordinates[0] * multiplier_degree))
    res = _encode_scaled_value(lat - last_lat, res)
    last_lat = lat

    lng = int(round(coordinates[1] * multiplier_degree))
    res = _encode_scaled_value(lng - last_lng, res)
    last_lng = lng

    return "".join(res)

def _encode_header(precision: int, res: np.array([], dtype=str)):
    if precision < 0 or precision > 15:
        raise ValueError("Precision is out of range.")
    
    res = _encode_unsigned_varint(FORMAT_VERSION, res)
    res = _encode_unsigned_varint(precision, res)

    return res
    
def _encode_scaled_value(value: int, res: np.array([], dtype=str)):
    # Encode "value" into a sequence of characters
    negative = value < 0

    value = value << 1
    if negative:
        value = ~value

    res = _encode_unsigned_varint(value, res)

    return res

def _encode_unsigned_varint(value: int, res: np.array([], dtype=str)):
    # Variable integer encoding
    while value > 0x1F:
        pos = (value & 0x1F) | 0x20
        res = np.append(res, ENCODING_TABLE[pos])
        value >>= 5
    
    res = np.append(res, ENCODING_TABLE[value])
    
    return res

def _decode(encoded: str, is_here: bool):
    last_lat = last_lng = 0

    decoded_values = np.empty(0, dtype=np.uint)
    decoded_values = _decode_unsigned_values(encoded, decoded_values)
    
    precision = _decode_header(decoded_values)
    factor_degree = 10.0 ** precision

    decoded_values = np.delete(decoded_values, [0, 1])

    if is_here:
        coordinates = np.empty((0, 2), dtype=float)
    else:
        coordinates = np.array([], dtype=float)
    
    for i in range(decoded_values.shape[0]):
        if i == len(decoded_values)-1:
            break
        if i%2 == 0:
            last_lat += _to_signed(decoded_values[i])
            last_lng += _to_signed(decoded_values[i+1]) 
            if is_here:
                coordinates = np.append(coordinates, [[last_lat/factor_degree, last_lng/factor_degree]], axis=0)
            else:
                coordinates = np.append(coordinates, [last_lat/factor_degree, last_lng/factor_degree])
    
    return coordinates

def _decode_unsigned_values(encoded: str, decoded_values: np.array([], dtype=np.uint)):
    result = shift = 0

    for char in encoded:
        value = _decode_char(char)

        result |= (value & 0x1F) << shift
        if (value & 0x20) == 0:
            decoded_values = np.append(decoded_values, result)
            result = shift = 0
        else:
            shift += 5

    if shift > 0:
        raise ValueError("Invalid encoding.")
    
    return decoded_values

def _decode_char(char: str):
    # Decode a single char to its corresponding value
    char_value = ord(char)

    try:
        value = DECODING_TABLE[char_value - 45]
    except IndexError:
        raise ValueError("Invalid encoding.")
    if value < 0:
        raise ValueError("Invalid encoding.")
    return value

def _decode_header(decoded_values: np.array([], dtype=np.uint)):
    version = decoded_values[0]
    if version != FORMAT_VERSION:
        raise ValueError("Invalid format version.")
    
    value = decoded_values[1]
    precision = value & 15

    return precision

def _to_signed(value: int):
    # Decode the sign of an unsigned value
    if value & 1:
        value = ~value
    value >>= 1
    return value