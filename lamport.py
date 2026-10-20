"""
Simulasi Lamport Timestamps untuk 3 proses (P1, P2, P3)

Aturan Lamport:
  1. Local event : C = C + 1
  2. Send event  : C = C + 1, lalu kirim pesan dengan timestamp C
  3. Receive     : C = max(C_lokal, ts_pesan) + 1
"""

from dataclasses import dataclass, field

@dataclass
class Event:
    process: str
    kind: str         
    timestamp: int
    desc: str
    msg_id: str = ""


@dataclass
class Process:
    name: str
    clock: int = 0
    log: list = field(default_factory=list)

    def local(self, desc):
        self.clock += 1
        e = Event(self.name, "local", self.clock, desc)
        self.log.append(e)
        return e

    def send(self, msg_id, to):
        self.clock += 1
        e = Event(self.name, "send", self.clock, f"kirim {msg_id} ke {to}", msg_id)
        self.log.append(e)
        return e, self.clock  # (event, timestamp yang dibawa pesan)

    def receive(self, msg_id, sender, ts_msg):
        before = self.clock
        self.clock = max(self.clock, ts_msg) + 1
        e = Event(
            self.name, "receive", self.clock,
            f"terima {msg_id} dari {sender} (max({before},{ts_msg})+1)", msg_id,
        )
        self.log.append(e)
        return e


def run_scenario():
    P = {n: Process(n) for n in ("P1", "P2", "P3")}
    in_transit = {}  # msg_id -> (sender, ts)

    steps = [
        ("P1", "local", "hitung data"),
        ("P1", "send", "m1", "P2"),
        ("P3", "local", "baca sensor"),
        ("P2", "local", "update state"),
        ("P2", "receive", "m1"),
        ("P2", "send", "m2", "P3"),
        ("P3", "send", "m3", "P1"),
        ("P3", "receive", "m2"),
        ("P1", "receive", "m3"),
        ("P1", "send", "m4", "P2"),
        ("P2", "receive", "m4"),
        ("P3", "local", "tulis log"),
    ]

    all_events = []
    for s in steps:
        p, kind = s[0], s[1]
        if kind == "local":
            all_events.append(P[p].local(s[2]))
        elif kind == "send":
            e, ts = P[p].send(s[2], s[3])
            in_transit[s[2]] = (p, ts)
            all_events.append(e)
        else:
            sender, ts = in_transit[s[2]]
            all_events.append(P[p].receive(s[2], sender, ts))
    return P, all_events


def verify(P, events):
    ok = True
    print("\n=== VERIFIKASI ===")

    for name, proc in P.items():
        ts = [e.timestamp for e in proc.log]
        good = all(a < b for a, b in zip(ts, ts[1:]))
        ok &= good
        print(f"[{'OK' if good else 'GAGAL'}] {name}: timestamp naik ketat {ts}")

    sends = {e.msg_id: e for e in events if e.kind == "send"}
    recvs = {e.msg_id: e for e in events if e.kind == "receive"}
    for m, s in sends.items():
        r = recvs[m]
        good = s.timestamp < r.timestamp
        ok &= good
        print(f"[{'OK' if good else 'GAGAL'}] {m}: send({s.process})={s.timestamp} < receive({r.process})={r.timestamp}")

    print("\nHasil akhir:", "KONSISTEN (clock condition terpenuhi)" if ok else "TIDAK KONSISTEN")
    return ok


def main():
    P, events = run_scenario()

    print("=== LOG EVENT (urutan eksekusi) ===")
    print(f"{'Proses':<7}{'Jenis':<10}{'TS':<5}Keterangan")
    print("-" * 60)
    for e in events:
        print(f"{e.process:<7}{e.kind:<10}{e.timestamp:<5}{e.desc}")

    print("\n=== TIMELINE PER PROSES ===")
    for name, proc in P.items():
        print(f"{name}: " + " -> ".join(f"{e.kind[0].upper()}{e.timestamp}" for e in proc.log))
    print("(L=local, S=send, R=receive)")

    verify(P, events)

    print("\n=== TOTAL ORDERING (timestamp, lalu id proses) ===")
    for i, e in enumerate(sorted(events, key=lambda x: (x.timestamp, x.process)), 1):
        print(f"{i:>2}. ({e.timestamp},{e.process}) {e.desc}")


if __name__ == "__main__":
    main()
