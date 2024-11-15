---
title: TMDb Settings (v1)
description: >
    How to connect TCM to TheMovieDatabase (TMDb).
---

# TMDb

## Background

This is an optional YAML section of your [global preferences file](...)
(`preferences.yml`) for outlining how TCM interacts with the public database
service, [TMDb](themoviedb.org). TMDb is used for many things by TCM, but
notably the following:

- Automatically downloading source image files for use in title cards
- Automatically downloading logos for title cards and summaries
- Automatically adding episode title translations to data files

## Recommended Setup

```yaml title="preferences.yml"
tmdb:
  api_key: # (1)!
```

1. Place your own TMDb-provided API key here

