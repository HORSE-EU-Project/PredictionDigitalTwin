```markdown
## Monitor Docker Containers with cAdvisor, Prometheus, and Grafana

Make sure Docker and Docker Compose are installed on your system if they are not already.

Pull the necessary Docker images for cAdvisor, Prometheus, and Grafana:
```sh
docker pull gcr.io/cadvisor/cadvisor:latest
docker pull prom/prometheus:latest
docker pull grafana/grafana:latest
```

Create or update your `docker-compose.yml` file to include Grafana:
```yaml
version: '3.2'

services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:rw
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro

  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    depends_on:
      - cadvisor

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "7070:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=yourpassword
    volumes:
      - grafana-storage:/var/lib/grafana
    depends_on:
      - prometheus

volumes:
  grafana-storage:
```

Ensure your `prometheus.yml` file configures Prometheus to scrape metrics from cAdvisor:
```yaml
scrape_configs:
  - job_name: 'cadvisor'
    scrape_interval: 5s
    static_configs:
      - targets: ['cadvisor:8080']
```

Run the following command to start the services:
```sh
docker-compose up -d
```

Check that all containers (cAdvisor, Prometheus, and Grafana) are running:
```sh
docker-compose ps
```
You should see all containers listed as "Up".

Open your web browser and navigate to:
- **Prometheus**: `http://localhost:9090`
- **cAdvisor**: `http://localhost:8080`
- **Grafana**: `http://localhost:7070` (Login with `admin` as the username and `yourpassword` as the password)

Configure Grafana to Use Prometheus:
1. **Login to Grafana**: Go to `http://localhost:3000` and log in.
2. **Add Prometheus as a Data Source**:
   - Navigate to `Configuration` > `Data Sources`.
   - Click `Add data source` and select `Prometheus`.
   - Set the URL to `http://prometheus:9090`.
   - Click `Save & Test` to ensure Prometheus is connected.
3. **Import a Dashboard**:
   - Navigate to `Create` > `Import`.
   - You can import a pre-built dashboard by entering its ID or uploading a JSON file.

Now you can create custom dashboards in Grafana to visualize the Docker container metrics collected by cAdvisor and stored in Prometheus.
```

You can generate load using:
```
docker run -it --name cpustress --rm containerstack/cpustress --cpu 4 --timeout 30s --metrics-brief
```

Feel free to copy the entire block above and use it as needed! 😊
