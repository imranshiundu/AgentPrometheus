# Hardware & Technical Requirements

To run the fully upgraded Agent Prometheus system—especially with OpenHands spinning up sandboxed coding environments and multiple agents running concurrently—power is required.

---

## 🖥 VPS & Hardware Specifications

Because the "brain" computation is offloaded to APIs (OpenAI, Claude, Gemini), you do not need an expensive GPU. However, you do need enough RAM and CPU to run multiple heavy Docker containers, vector databases, and Python environments simultaneously.

### 1. The Minimum Specs (Functional)
*   **CPU:** 4 vCPUs
*   **RAM:** 8 GB
*   **Storage:** 40 GB SSD (Docker images for OpenHands and AutoGPT are massive).

### 2. The Recommended Specs (Production-Ready)
*   **CPU:** 8 vCPUs
*   **RAM:** 16 GB (Highly recommended for sandboxed code compilation).
*   **Storage:** 80 GB NVMe SSD.

### 3. Recommended Cloud Providers
*   **Hetzner:** CPX31 or CPX41 tier (Extremely cost-effective).
*   **DigitalOcean:** 16GB RAM Droplet.
*   **AWS EC2:** t3.xlarge.

---

## 📱 Compatible Devices

Agent Prometheus is containerized and highly portable:

-   **Cloud VPS:** Any standard Linux server (Ubuntu 22.04 or 24.04 LTS is the gold standard).
-   **Mac OS:** Apple Silicon (M1/M2/M3/M4) or Intel Macs using Docker Desktop.
-   **Windows PC:** Windows 10/11 running via **WSL2** (Windows Subsystem for Linux) with Docker Desktop.
-   **Local Linux Machines:** Native Docker on Debian, Arch, Fedora, etc.
