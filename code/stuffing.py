# import zlib removed

def calculate_crc(data_bytes):
    """
    Calculates CRC-32 for the given byte data using the standard IEEE 802.3 polynomial.
    Returns the CRC as a 32-bit integer.
    """
    crc = 0xFFFFFFFF
    poly = 0xEDB88320 # Reverse polynomial for LSB-first (standard CRC-32)
    
    for byte in data_bytes:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
                
    return crc ^ 0xFFFFFFFF

def bit_stuffing(bit_string):
    """
    Applies HDLC bit stuffing: inserts a '0' after every five consecutive '1's.
    Input: string of '0's and '1's.
    Output: stuffed string.
    """
    stuffed = ""
    count = 0
    for bit in bit_string:
        stuffed += bit
        if bit == '1':
            count += 1
            if count == 5:
                stuffed += '0'
                count = 0
        else:
            count = 0
    return stuffed

def bit_destuffing(stuffed_bit_string):
    """
    Removes HDLC bit stuffing: removes '0' that follows five consecutive '1's.
    Input: stuffed string of '0's and '1's.
    Output: original string.
    """
    destuffed = ""
    count = 0
    i = 0
    while i < len(stuffed_bit_string):
        bit = stuffed_bit_string[i]
        destuffed += bit
        
        if bit == '1':
            count += 1
            if count == 5:
                # Check if next bit is 0 (stuffing bit)
                if i + 1 < len(stuffed_bit_string) and stuffed_bit_string[i+1] == '0':
                    i += 1 # Skip the stuffed '0'
                count = 0 # Reset count after handling the sequence
        else:
            count = 0
        i += 1
    return destuffed

def bytes_to_bits(data_bytes):
    """Convert bytes to a binary string representation."""
    return ''.join(f'{byte:08b}' for byte in data_bytes)

def bits_to_bytes(bit_string):
    """Convert binary string representation back to bytes."""
    # Pad with zeros if not multiple of 8 (though protocol should handle alignment)
    if len(bit_string) % 8 != 0:
        # In a real scenario we might need padding handling, 
        # but here we assume frames are byte-aligned before stuffing
        pass 
        
    byte_array = bytearray()
    for i in range(0, len(bit_string), 8):
        byte_chunk = bit_string[i:i+8]
        if len(byte_chunk) < 8:
            # Padding for the last chunk if necessary (shouldn't happen with correct framing)
            byte_chunk = byte_chunk.ljust(8, '0') 
        byte_array.append(int(byte_chunk, 2))
    return bytes(byte_array)

if __name__ == "__main__":
    # Test de validation du bit-stuffing demandé
    input_bits = "011111101111101111110111110"
    expected_stuffed = "0111110101111100111110101111100"
    
    stuffed = bit_stuffing(input_bits)
    destuffed = bit_destuffing(stuffed)
    
    print(f"Input:     {input_bits}")
    print(f"Stuffed:   {stuffed}")
    print(f"Expected:  {expected_stuffed}")
    print(f"Destuffed: {destuffed}")
    
    if stuffed == expected_stuffed and destuffed == input_bits:
        print("SUCCESS: Bit stuffing test passed.")
    else:
        print("FAILURE: Bit stuffing test failed.")

    
    print(f"CRC Input: {test_data}")
    print(f"CRC Calc:  {calculated:08X}")
    print(f"CRC Exp:   {expected_crc:08X}")
    
    if calculated == expected_crc:
        print("SUCCESS: CRC test passed.")
    else:
        print("FAILURE: CRC test failed.")
