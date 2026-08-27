
# <img src="avatar.svg" alt="alt text" width="50"/> Chrono S. Thompson: The Gonzo Historical Correspondent
Chrono S. Thompson is an autonomous agentic pipeline designed to solve the temporal disconnect between past records and modern context. Instead of treating historical archives as static encyclopedic entries, the architecture orchestrates a stateful multi-step workflow that:

1. **Fetches historical data** via an isolated Model Context Protocol (MCP) server.
2. **Performs editorial curation** using deterministic structured outputs (Pydantic).
3. **Discovers contemporary parallels** via real-time search grounding.
4. **Drafts high-engagement prose** in the authentic, visceral voice of Gonzo journalism.
5. **Persists and distributes** daily dispatches automatically.

---

## Architecture Overview

Chrono S. Thompson consists of several interconnected nodes that work together to create compelling historical narratives:

1. **Data Fetcher Node**: Retrieves historical data from an isolated MCP server.
2. **Curator & Ranker Node**: Selects the most interesting historical events and generates editorial hooks.
3. **Real-Time Correlator**: Finds contemporary parallels for the selected event.
4. **Gonzo Journalist Node**: Produces high-engagement prose in Gonzo-style journalism.

---

## Getting Started

### Prerequisites
- Python 3.8+
- Required libraries: `fastapi`, `pydantic`, `uvicorn`

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/chrono-s-thompson.git
   cd chrono-s-thompson
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the pipeline:
   ```bash
   uvicorn src.main:app --reload
   ```

### Configuration
The `settings.py` file contains all necessary configuration settings. Ensure that you have set up your API keys and other environment variables.

---

## Contributing

We welcome contributions! Please follow these steps to contribute to the project:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/AmazingFeature`).
3. Make your changes and commit them (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a pull request.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.