"""
Source file with functions & classes for hard-drive based data loading for deep learning.

# Functionalities

## Writing
Use write_split_data() to write multiple packets of byte data, each going to a different
file (called bins).

## Reading
The class SplitDataLoader provides the functions required for loading data. It supports
length calculation and indexing.
"""

import struct
import shutil
import random

from typing import Iterable, BinaryIO
from pathlib import Path

# Used for storing size (uint32)
STRUCT_NUM_FORMAT = "<I"
# Number of bytes required to store size
STRUCT_NUM_FORMAT_SIZE = struct.calcsize(STRUCT_NUM_FORMAT)


def struct_pack_write(writer: BinaryIO, number: int) -> None:
    writer.write(struct.pack(STRUCT_NUM_FORMAT, number))


def read_struct_unpack(reader: BinaryIO) -> tuple[bool, int]:
    data = reader.read(STRUCT_NUM_FORMAT_SIZE)
    if not data:
        return False, 0
    number = struct.unpack("<I", data)[0]
    return True, number


def get_index_file(data_dir_path: Path) -> Path:
    return data_dir_path / "index.bin"


def get_bin_file_for_index(data_dir_path: Path, index: int) -> Path:
    file_name_pattern = "part{:08d}.bin"
    return data_dir_path / file_name_pattern.format(index)


def write_split_data(
    target_dir: str,
    input_sequence: Iterable[bytes],
    splits: int = 256,
    shuffle: bool = False,
    start_clean: bool = False,
) -> None:
    """
    Write a sequence of data to multiple bins.

    target_dir: path to store bin files and index files

    This function will send each packet from input_sequence to a different bin. If shuffle
    is true, order of bins will be shuffled. This does not shuffle the actual sequence.

    An index file is used to keep track of the bin-index and position of each packet.
    """
    if start_clean:
        shutil.rmtree(target_dir, ignore_errors=True)

    data_dir_path = Path(target_dir)
    # Create if the dir does not exist
    data_dir_path.mkdir(parents=True, exist_ok=True)
    # To be used for storing index data.
    # Each step involve writing (index, position, length)
    index_file_path = get_index_file(data_dir_path)

    # Indexes to be used for when shuffle is used.
    indexes = []
    if shuffle:
        indexes = list(range(splits))
        random.shuffle(indexes)

    # For every step, we update the index data
    index_file = open(index_file_path, "wb")

    for idx, data in enumerate(input_sequence):
        if shuffle:
            idx = indexes[idx]

        bin_file = get_bin_file_for_index(data_dir_path, idx)

        # Get binary file for this data
        position = 0
        length = len(data)
        # Write data (size prefixed)
        with open(bin_file, "ab") as writer:
            # Get current position
            position = writer.tell()
            struct_pack_write(writer, length)
            writer.write(data)

        # Update index file
        for value in (idx, position, length):
            struct_pack_write(index_file, value)

    index_file.close()


class SplitDataLoader:
    def __init__(self, data_dir: str) -> None:
        self.data_dir_path = Path(data_dir)
        self.index_file = get_index_file(self.data_dir_path)
        # Index file contains a triplet of (index, position, length), each in U32
        self.index_packet_size = 3 * 4

    def __len__(self) -> int:
        """
        Calculate and return length of dataset.

        Length calculated based on the size of the index file.
        """
        index_file_size = self.index_file.stat().st_size
        count = index_file_size // self.index_packet_size
        return count

    def __getitem__(self, idx: int) -> bytes:
        """
        Return packet at the given index idx.

        First get the info regarding the packet's bin-index, position, and length from
        the index file. Then read the packet from the bin file based on position and
        length.
        """
        location = self.index_packet_size * idx
        values = []

        # Get index, position, length from index-file
        with open(self.index_file, "rb") as reader:
            reader.seek(location)
            for value_idx in range(3):
                valid, value = read_struct_unpack(reader)
                if not valid:
                    raise ValueError(f"unable to read value for {idx=} {value_idx=}")
                values.append(value)

        # Get the actual data packet from the bin file
        index, position, length = values
        bin_file = get_bin_file_for_index(self.data_dir_path, index)
        data = b""
        with open(bin_file, "rb") as reader:
            reader.seek(position)
            valid, packet_size = read_struct_unpack(reader)
            if not valid:
                raise ValueError(f"unable to read size for {idx=}")
            if packet_size != length:
                raise ValueError(f"Size mismatch {packet_size} != {length}")
            data = reader.read(length)
        return data
