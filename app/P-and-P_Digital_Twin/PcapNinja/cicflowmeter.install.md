git clone https://github.com/hieulw/cicflowmeter
cd cicflowmeter
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
source .venv/bin/activate
# cicflowmeter -f dns.pcap -c output.txt
