#!/bin/bash

# Dohvati sve cacheove
caches=$(gh actions-cache list --limit 100 | awk 'NR>1 {print $1}')

# Provjeri jesu li pronađeni cacheovi
if [ -z "$caches" ]; then
  echo "Nema pronađenih cacheova za brisanje."
else
  # Obrisi svaki cache
  for cache in $caches; do
    echo "Brišem cache: $cache"
    gh actions-cache delete "$cache" --confirm
  done
  echo "Svi cacheovi su obrisani."
fi

