FAQ!
-----------------------

Q1. How to I connect to test database without installing anything?

Assuming you cloned source code and have podman setup, just run bash commands:

```
> cd t/manual
T_PAUSE_ON_EXIT=1 ./02-src.o.o_scan_all.sh 
```

The commands will create Docker image, run the script in it and then wait any input to destroy the container.
It will also print instruction about how to connect the container.
Inside container you can use environ wrappers e.g. sc1/sql to connect to the postgres server.
