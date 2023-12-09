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

## Installation

Use pip. [Project](https://pypi.org/project/splitdataloader/) is available at PyPI.

```
pip install splitdataloader
```

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
    for data in loader.iterate_binwise(shuffle=True):
        do_something(data)
```

## Multiprocessing Queue Based Iterator
If the loading takes too much time, it is probably a good idea to run the
loading part in a separate process. If it is possible to refactor the entity
that produces the batches as a generator, `splitdataloader.MpQItr` can
be used to handle loading. Data will be loaded to an internal queue while
it is being processed in the main process.

```python
from splitdataloader import MpQItr

# a tuple, class, or whatever that handles the batch
class BatchType:
    ...

# a generator function that produces the batches
def batch_generator(...) -> Iterator[BatchType]:
    ...

def batch_wise_processing(...):
    # Multi-processing queue based iterator
    queued_batch_iterator = MpQItr[BatchType](
        batch_generator,  # the generator function
        args... # args or kwargs to the generator function
    )
    for batch in queued_batch_iterator:
        do_something_with(batch)
```
