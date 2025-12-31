import time
import struct
import threading
import queue
from canal import Canal
from stuffing import bit_stuffing, bit_destuffing, calculate_crc, bytes_to_bits, bits_to_bytes


FLAG = b'\x7E' 

class Frame:
    def __init__(self, seq_num, data=b'', is_ack=False):
        self.seq_num = seq_num
        self.data = data
        self.is_ack = is_ack

    def to_bytes(self):
        # Format: [Type(1B) | Seq(4B) | Len(2B) | Data | CRC(4B)]
        
        type_byte = 1 if self.is_ack else 0
        header = struct.pack('!B I H', type_byte, self.seq_num, len(self.data))
        payload = header + self.data
        crc = calculate_crc(payload)
        return payload + struct.pack('!I', crc)

    @staticmethod
    def from_bytes(raw_bytes):
        if len(raw_bytes) < 11: # Min size: 1+4+2+4 = 11
            return None
        
        try:
            # Read header to get length
            type_byte, seq_num, length = struct.unpack('!B I H', raw_bytes[:7])
            
            # Calculate expected total size
            expected_size = 7 + length + 4
            
            # Check if we have enough bytes
            if len(raw_bytes) < expected_size:
                return None
            
            # Truncate to expected size (ignoring padding)
            frame_bytes = raw_bytes[:expected_size]
            
            # Verify CRC
            payload = frame_bytes[:-4]
            received_crc = struct.unpack('!I', frame_bytes[-4:])[0]
            
            if calculate_crc(payload) != received_crc:
                return None # CRC Error
            
            data = frame_bytes[7:-4]
            return Frame(seq_num, data, is_ack=(type_byte == 1))
            
        except struct.error:
            return None

class Sender:
    def __init__(self, canal, window_size=4, timeout=0.5):
        self.canal = canal
        self.window_size = window_size
        self.timeout = timeout
        self.next_seq_num = 0
        self.base = 0
        self.buffer = []
        self.timers = {}
        self.lock = threading.Lock()
        self.running = True
        self.target_callback = None # Must be set before sending
        
        # Stats
        self.frames_sent = 0
        self.frames_retransmitted = 0
        self.acks_received = 0

    def send_data(self, data_chunks):
        self.buffer = data_chunks
        total_frames = len(data_chunks)
        
        print(f"[{time.strftime('%H:%M:%S')}] Début de transmission. {total_frames} trames à envoyer.")
        
        while self.base < total_frames and self.running:
            with self.lock:
                # Send frames within window
                while self.next_seq_num < self.base + self.window_size and self.next_seq_num < total_frames:
                    self.send_frame(self.next_seq_num)
                    self.next_seq_num += 1
            time.sleep(0.01) # Prevent CPU hogging

        print(f"[{time.strftime('%H:%M:%S')}] Transmission terminée côté émetteur.")

    def send_frame(self, seq_num):
        frame = Frame(seq_num, self.buffer[seq_num])
        raw_frame = frame.to_bytes()
        
        # Bit Stuffing & Framing
        bits = bytes_to_bits(raw_frame)
        stuffed_bits = bit_stuffing(bits)
        # Add Flags
        final_frame = FLAG + bits_to_bytes(stuffed_bits) + FLAG
        
        print(f"[{time.strftime('%H:%M:%S')}] Envoi trame {seq_num}")
        
        if self.target_callback:
            self.canal.envoyer(final_frame, self.target_callback)
        else:
            print("Erreur: target_callback non configuré")
            
        self.frames_sent += 1
        
        # Start Timer
        if seq_num in self.timers:
            self.timers[seq_num].cancel()
        self.timers[seq_num] = threading.Timer(self.timeout, self.handle_timeout, args=[seq_num])
        self.timers[seq_num].start()

    def receive_ack(self, ack_num):
        with self.lock:
            print(f"[{time.strftime('%H:%M:%S')}] Reçu ACK {ack_num}")
            self.acks_received += 1
            
            # Cumulative ACK
            if ack_num >= self.base:
                # Cancel timers for acknowledged frames
                for i in range(self.base, ack_num + 1):
                    if i in self.timers:
                        self.timers[i].cancel()
                        del self.timers[i]
                
                self.base = ack_num + 1

    def handle_timeout(self, seq_num):
        with self.lock:
            # Check if still valid (might have been acked just now)
            if seq_num >= self.base:
                print(f"[{time.strftime('%H:%M:%S')}] Timeout trame {seq_num}. Retransmission fenêtre à partir de {self.base}.")
                # Go-Back-N: Retransmit all from base
                # Reset next_seq_num to base to trigger retransmission loop
                self.next_seq_num = self.base
                self.frames_retransmitted += 1

class Receiver:
    def __init__(self, output_file):
        self.expected_seq_num = 0
        self.output_file = output_file
        self.received_data = {}
        self.lock = threading.Lock()
        self.ack_target = None # Function to call to send ACK (via canal)

    def receive(self, raw_packet):
        # Check Flags
        if not (raw_packet.startswith(FLAG) and raw_packet.endswith(FLAG)):
            return # Invalid framing
        
        # Remove Flags
        stuffed_content = raw_packet[1:-1]
        
        # Destuffing
        try:
            stuffed_bits = bytes_to_bits(stuffed_content)
            destuffed_bits = bit_destuffing(stuffed_bits)
            frame_bytes = bits_to_bytes(destuffed_bits)
        except Exception:
            return # Destuffing error
            
        frame = Frame.from_bytes(frame_bytes)
        
        if frame:
            with self.lock:
                if frame.seq_num == self.expected_seq_num:
                    print(f"[{time.strftime('%H:%M:%S')}] Réception correcte trame {frame.seq_num}")
                    self.received_data[frame.seq_num] = frame.data
                    self.expected_seq_num += 1
                    
                    # Send ACK
                    self.send_ack(frame.seq_num)
                elif frame.seq_num < self.expected_seq_num:
                    # Duplicate/Old frame, re-ACK
                    print(f"[{time.strftime('%H:%M:%S')}] Trame dupliquée {frame.seq_num}. Renvoi ACK.")
                    self.send_ack(frame.seq_num)
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] Trame hors séquence {frame.seq_num} (Attendu: {self.expected_seq_num}). Ignorée.")
                    if self.expected_seq_num > 0:
                        self.send_ack(self.expected_seq_num - 1)

    def send_ack(self, seq_num):
        if not self.ack_target: return
        
        ack_frame = Frame(seq_num, is_ack=True)
        raw_ack = ack_frame.to_bytes()
        
        # Stuffing for ACK
        bits = bytes_to_bits(raw_ack)
        stuffed = bit_stuffing(bits)
        final = FLAG + bits_to_bytes(stuffed) + FLAG
        
        # Send via return channel
        self.ack_target(final)

# Main Execution
def run_scenario(name, prob_err, prob_loss, delay_max, timeout):
    print(f"\n--- Scénario: {name} ---")
    print(f"Params: Err={prob_err}, Loss={prob_loss}, Delay={delay_max}ms, Timeout={timeout}s")
    
    # Setup
    canal_aller = Canal(prob_err, prob_loss, delay_max)
    canal_retour = Canal(prob_err, prob_loss, delay_max)
    
    sender = Sender(canal_aller, window_size=5, timeout=timeout)
    receiver = Receiver("output.txt")
    
    sender.target_callback = receiver.receive
   
    def ack_delivery(packet):
        
        if not (packet.startswith(FLAG) and packet.endswith(FLAG)): return
        try:
            destuffed = bit_destuffing(bytes_to_bits(packet[1:-1]))
            frame_bytes = bits_to_bytes(destuffed)
            frame = Frame.from_bytes(frame_bytes)
            if frame and frame.is_ack:
                sender.receive_ack(frame.seq_num)
        except:
            pass

    def receiver_send_ack_wrapper(packet):
        canal_retour.envoyer(packet, ack_delivery)
        
    receiver.ack_target = receiver_send_ack_wrapper

   
    with open("../message.txt", "rb") as f:
        content = f.read()
    
    # Segment
    CHUNK_SIZE = 100
    chunks = [content[i:i+CHUNK_SIZE] for i in range(0, len(content), CHUNK_SIZE)]
    
    start_time = time.time()
    sender.send_data(chunks)
    
    
    time.sleep(2) 
    while sender.base < len(chunks):
        time.sleep(1)
        if time.time() - start_time > 60: 
            print("Force stop.")
            break
            
    end_time = time.time()
    
    # Verify
    received_content = b"".join([receiver.received_data[i] for i in range(len(chunks)) if i in receiver.received_data])
    success = (received_content == content)
    
    print(f"\nRésultats {name}:")
    print(f"Succès: {success}")
    print(f"Frames envoyées: {sender.frames_sent}")
    print(f"Frames retransmises: {sender.frames_retransmitted}")
    print(f"ACK reçus: {sender.acks_received}")

    print(f"Durée totale: {end_time - start_time:.2f} s")
    
    return {
        "name": name,
        "success": success,
        "sent": sender.frames_sent,
        "retrans": sender.frames_retransmitted,
        "acks": sender.acks_received,
        "duration": end_time - start_time
    }

if __name__ == "__main__":
    results = []
    
    # Scenarios
    # 1. Canal parfait
    results.append(run_scenario("Parfait", 0.0, 0.0, 0, 0.5))
    
    # 2. Canal bruité
    results.append(run_scenario("Bruité", 0.05, 0.1, 200, 0.5))
    
    # 3. Canal instable
    results.append(run_scenario("Instable", 0.10, 0.15, 300, 0.5))
    
    # 4. Influence délai
    results.append(run_scenario("Delai Court", 0.0, 0.0, 50, 0.2))
    results.append(run_scenario("Delai Moyen", 0.0, 0.0, 180, 0.2))
    results.append(run_scenario("Delai Long", 0.0, 0.0, 300, 0.2))

    # Summary
    print("\n" + "="*80)
    print(f"{'SCÉNARIO':<15} | {'SUCCÈS':<8} | {'ENVOIS':<8} | {'RETRANS':<8} | {'ACKS':<8} | {'DURÉE (s)':<10}")
    print("-" * 80)
    for r in results:
        print(f"{r['name']:<15} | {str(r['success']):<8} | {r['sent']:<8} | {r['retrans']:<8} | {r['acks']:<8} | {r['duration']:<10.2f}")
    print("="*80)
