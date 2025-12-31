import random
import time
import threading
import queue

class Canal:
    def __init__(self, prob_erreur=0.05, prob_perte=0.10, delai_max=200):
        self.prob_erreur = prob_erreur
        self.prob_perte = prob_perte
        self.delai_max = delai_max / 1000.0
        self.last_arrival_time = 0
        self.lock = threading.Lock()
        
        # Priority Queue for delivery: (arrival_time, counter, packet, callback)
        self.queue = queue.PriorityQueue()
        self.counter = 0
        
        # Start worker thread
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def envoyer(self, trame, destination_callback):
        if random.random() < self.prob_perte:
            return

        trame_finale = bytearray(trame)
        if random.random() < self.prob_erreur:
            if len(trame_finale) > 0:
                idx = random.randint(0, len(trame_finale) - 1)
                bit_idx = random.randint(0, 7)
                trame_finale[idx] ^= (1 << bit_idx)

        delai = random.uniform(0, self.delai_max)
        now = time.time()
        
        with self.lock:
            arrival_time = now + delai
            # Ensure strict FIFO order
            if arrival_time < self.last_arrival_time:
                arrival_time = self.last_arrival_time + 0.00001
            self.last_arrival_time = arrival_time
            count = self.counter
            self.counter += 1
            
        self.queue.put((arrival_time, count, bytes(trame_finale), destination_callback))

    def _worker(self):
        while self.running:
            try:
                arrival_time, _, packet, callback = self.queue.get(timeout=0.1)
            except queue.Empty:
                continue
            
            now = time.time()
            wait_time = arrival_time - now
            
            if wait_time > 0:
                time.sleep(wait_time)
            
            try:
                callback(packet)
            except Exception as e:
                print(f"Error in callback: {e}")
            
            self.queue.task_done()
