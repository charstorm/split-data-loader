# split-data-loader

This package contains simple utility functions related to writing and reading
data (typically related to machine learning) using multiple files.

There are mainly two extremes when dealing with data.

1. All the data in a single file - This is good for sequential access,
   but can be cumbersome to shuffle data when reading.
2. Each frame in its own file - This creates too many tiny files
   and can be difficult to scale.

This library uses an intermediate approach. The entire dataset is split and
stored in multiple files (eg: N = 128) called bins. It allows easy shuffling of
data and parallel processing when required.

This library also uses an index file to keep track of the order and location of
each packet. It allows index based random lookup of all the input packets,
distributed among all the bin files.


## Writing Data
Use `write_split_data` to write data to a target directory.
   
```python
from splitdataloader import write_split_data

def example_writer(...):
    # Get the data source
    data_source: Iterable[bytes] = some_source()
    target_dir = "tmp/training_data"
    write_split_data(target_dir, data_source, splits=128)
```

## Reading Data
This is the main objective of this library. The class `SplitDataLoader` handles
the loading of data. 
It supports the following:
1. Getting length using `len()`
2. Random indexing using `[]`
3. Data iteration (binwise), with support for shuffling

```python
from splitdataloader import SplitDataLoader

def example_loader(...):
    # Get the data source
    data_dir = "tmp/training_data"
    loader = SplitDataLoader(data_dir)
    # Supports len()
    print(len(loader))
    # Supports indexing
    data  = loader[2]
    # Supports iteration
    for data in loader.iterate_binwise():
        do_something(data)
```

