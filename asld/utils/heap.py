import heapq


class Heap:

    def __init__(self):
        self.heap = []

    def __bool__(self):
        return bool(self.heap)

    def __len__(self):
        return len(self.heap)

    def peek(self):
        return self.heap[0]

    def peekValue(self):
        (_, v) = self.heap[0]
        return v

    def peekKey(self):
        (k, _) = self.heap[0]
        return k

    def push(self, k, v):
        heapq.heappush(self.heap, (k, v))

    def pop(self):
        return heapq.heappop(self.heap)

    def isEmpty(self):
        return len(self.heap) == 0

    def clear(self):
        self.heap = []


class MaxHeap(Heap):

    def push(self, k, v):
        return heapq.heappush(self.heap, (-k, v))

    def pop(self):
        (k, v) = heapq.heappop(self.heap)
        return (-k, v)
