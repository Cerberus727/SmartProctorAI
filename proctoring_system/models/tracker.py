from collections import OrderedDict
import numpy as np
from config.settings import MAX_TRACKING_DISAPPEARED

MAX_DISTANCE = 120.0
MIN_HITS = 3

class SimpleTracker:
    def __init__(self):
        self.next_object_id = 0
        self.objects = OrderedDict() # Stores (centroid, rect)
        self.disappeared = OrderedDict()
        self.hits = OrderedDict()

    def register(self, centroid, rect):
        self.objects[self.next_object_id] = (centroid, rect)
        self.disappeared[self.next_object_id] = 0
        self.hits[self.next_object_id] = 1
        self.next_object_id += 1

    def deregister(self, object_id):
        del self.objects[object_id]
        del self.disappeared[object_id]
        del self.hits[object_id]

    def _get_active_objects(self):
        # Only return objects that have been seen consistently
        return {k: v for k, v in self.objects.items() if self.hits[k] >= MIN_HITS}

    def update(self, rects):
        if len(rects) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > MAX_TRACKING_DISAPPEARED:
                    self.deregister(object_id)
            return self._get_active_objects()

        input_centroids = np.zeros((len(rects), 2), dtype="int")
        input_rects = []
        for (i, (startX, startY, endX, endY)) in enumerate(rects):
            cX = int((startX + endX) / 2.0)
            cY = int((startY + endY) / 2.0)
            input_centroids[i] = (cX, cY)
            input_rects.append((startX, startY, endX, endY))

        if len(self.objects) == 0:
            for i in range(0, len(input_centroids)):
                self.register(input_centroids[i], input_rects[i])
        else:
            object_ids = list(self.objects.keys())
            # Extract just centroids for distance calc
            object_centroids = [obj[0] for obj in self.objects.values()]

            D = np.linalg.norm(np.array(object_centroids)[:, np.newaxis] - input_centroids, axis=2)

            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]

            used_rows = set()
            used_cols = set()

            for (row, col) in zip(rows, cols):
                if row in used_rows or col in used_cols:
                    continue
                
                # Check max distance
                if D[row, col] > MAX_DISTANCE:
                    continue

                object_id = object_ids[row]
                self.objects[object_id] = (input_centroids[col], input_rects[col])
                self.disappeared[object_id] = 0
                self.hits[object_id] += 1

                used_rows.add(row)
                used_cols.add(col)

            unused_rows = set(range(0, D.shape[0])).difference(used_rows)
            unused_cols = set(range(0, D.shape[1])).difference(used_cols)

            if D.shape[0] >= D.shape[1]:
                for row in unused_rows:
                    object_id = object_ids[row]
                    self.disappeared[object_id] += 1
                    if self.disappeared[object_id] > MAX_TRACKING_DISAPPEARED:
                        self.deregister(object_id)
            else:
                for col in unused_cols:
                    self.register(input_centroids[col], input_rects[col])

        return self._get_active_objects()