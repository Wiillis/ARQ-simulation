# ARQ-simulation
#  Reliable Data Link Protocol: Go-Back-N Implementation

## Project Overview
This project implements a reliable Layer 2 (Data Link) communication protocol using the Go-Back-N (GBN) algorithm. It simulates data transmission over an unreliable channel, handling common network issues such as packet loss, bit errors, and transmission delays.

##  Key Technical Features
- **Flow Control**: Implementation of the Sliding Window mechanism (Go-Back-N).
- **Error Detection**: Cyclic Redundancy Check (CRC) for ensuring data integrity.
- **Data Transparency**: Implementation of Bit-Stuffing to handle frame delimitation.
- **Unreliable Channel Simulation**: Custom environment to simulate real-world network degradation (loss, corruption, latency).

## Project Structure
```
code/
  canal.py: Channel simulation (errors, packet loss, delays).
  stuffing.py: Functions for Bit-stuffing and CRC calculations.
  protocole.py: Core implementation of Sender, Receiver, and test scenarios.
  message.txt: Source file used for transmission tests.
```
- **rapport.md**: Detailed technical report on design choices and test results.

## How to Run
1. Navigate to the `code/` directory.
2. Run the simulation:
   ```bash
   python protocole.py
   ```
3. The results for 4 different network scenarios will be displayed in the terminal.
4. The transmitted data will be reconstructed in a file named `output.txt`.

## Configuration
Scenarios (error probability, loss rate, and delays) can be adjusted directly in the `if __name__ == "__main__":` block at the end of `protocole.py`.

