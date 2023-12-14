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

> [!NOTE]
> The "split" here has nothing to do with train/test split. It is expected that
> train/test split is done before writing data using the methods given here.

## Installation

Use pip. The [project](https://pypi.org/project/splitdataloader/) is available at PyPI.

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

During writing, data will be distributed among all the bins.

The function `write_split_data` is defined as follows.

```python
def write_split_data(
    target_dir: str,
    input_sequence: Iterable[bytes],
    splits: int = 256,
    shuffle: bool = False,
    start_clean: bool = False,
) -> None:
    ...
```

* `target_dir` - this is the directory where all bin files and index file will be stored
* `input_sequence` - input data source (corresponding to a single frame, not batch)
* `splits` - number of splits to use
* `shuffle` - if true, shuffle the order of bins when writing each frame
* `start_clean` - if true, clear the contents of the `target_dir` before start.
  Otherwise, new frames will be appended to the existing bins.


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

Here the method `iterate_binwise` is useful for shuffling data during the loading.
If shuffle is False, frames will be iterated in the same order they appear in the bins.

## Multiprocessing Queue Based Iterator
If the loading takes too much time, it is probably a good idea to run the
loading part in a separate process. If it is possible to refactor the entity
that produces the batches as a generator, `splitdataloader.MpQItr` can
be used to handle loading. Data will be loaded to an internal queue while
it is being processed in the main process.

```python
from splitdataloader import MpQItr

# A tuple, class, or whatever that handles the batch
class BatchType:
    ...

# A generator function that produces the batches
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

In the above, the `batch_generator` function should be provided by the user.
It should do the following:
1. load the data
2. pre-process (scaling, normalization, etc)
3. combine multiple frames into batches
4. yield the batch

This will make sure that all the pre-processing is handled by a separate process
and the main process only has to deal with the model training (or validation).
