# Installing Zoning.Space

Zoning.Space is written in Python, and uses `conda` for dependency management. To install Zoning.Space, first [install Anaconda](https://www.anaconda.com/download/).

Zoning.Space dependencies are listed in `environment.yml`. To create and activate a `conda` environment from `environment.yml`, run the following commands.

```
conda env create --name zoning.space --file environment.yml
source activate zoning.space
```

When dependencies change, update your environment:

```
conda env update --name zoning.space --file environment.yml
```

Zoning.Space is now installed.
