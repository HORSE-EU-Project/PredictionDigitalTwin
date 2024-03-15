# docker pull redislabs/redistimeseries

# docker build --no-cache --force-rm -t srv_image --file Dockerfile.srv_image .

# docker build --no-cache --force-rm -t my5gc --file ./Dockerfile_ogs .
# docker build --no-cache --force-rm -t my5gc_v2-3-2 --file ./Dockerfile_o5gs_v2-3-2 .
# docker build --no-cache --force-rm -t my5gc_v2-4-2 --file ./Dockerfile_o5gs_v2-4-2 .
docker build --no-cache --force-rm -t my5gc_v2-4-4 --file ./Dockerfile_o5gs_v2-4-4 .

# docker build --no-cache --force-rm -t myueransim_latest --file ./Dockerfile_uersim_latest .
# docker build --no-cache --force-rm -t myueransim_v3-1-9 --file ./Dockerfile_uersim_v3-1-9 .
docker build --no-cache --force-rm -t myueransim_v3-2-6 --file ./Dockerfile_uersim_v3-2-6 .


