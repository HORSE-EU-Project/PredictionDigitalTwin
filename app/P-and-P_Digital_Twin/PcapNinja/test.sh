#!/bin/bash

#demo=2

case "$demo" in
  1)
    attack="Low-level attack"
    ;;
  2)
    attack="Medium-level attack"
    ;;
  3)
    attack="High-level attack"
    ;;
  *)
    attack="Unknown attack level"
    ;;
esac

# Copy attack into TMP
TMP="$attack"

echo "attack=$attack"
