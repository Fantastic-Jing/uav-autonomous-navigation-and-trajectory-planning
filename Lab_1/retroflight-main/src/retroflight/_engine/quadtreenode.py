class QuadtreeNode:
    def __init__(self, x, y, w, h, depth=0, max_depth=5, max_objects=5):
        self.bounds = (x, y, w, h)
        self.depth = depth
        self.max_depth = max_depth
        self.max_objects = max_objects
        self.objects = []
        self.children = []

    def insert(self, ent):
        if self.children:
            index = self._get_quadrant(ent)
            if index is not None:
                self.children[index].insert(ent)
                return

        self.objects.append(ent)

        if len(self.objects) > self.max_objects and self.depth < self.max_depth:
            if not self.children:
                self._subdivide()
            i = 0
            while i < len(self.objects):
                obj = self.objects[i]
                index = self._get_quadrant(obj)
                if index is not None:
                    self.children[index].insert(obj)
                    self.objects.pop(i)
                else:
                    i += 1

    def query(self, x, y, w, h):
        results = []
        if not self._intersects(x, y, w, h):
            return results

        for obj in self.objects:
            if abs(obj.x - (x + w/2)) < w and abs(obj.y - (y + h/2)) < h:
                results.append(obj)

        if self.children:
            for child in self.children:
                results.extend(child.query(x, y, w, h))

        return results

    def _get_quadrant(self, ent):
        x, y, w, h = self.bounds
        mid_x = x + w / 2
        mid_y = y + h / 2

        top = ent.y < mid_y
        bottom = ent.y >= mid_y
        left = ent.x < mid_x
        right = ent.x >= mid_x

        if top and left: return 0
        if top and right: return 1
        if bottom and left: return 2
        if bottom and right: return 3
        return None

    def _subdivide(self):
        x, y, w, h = self.bounds
        hw, hh = w / 2, h / 2
        self.children = [
            QuadtreeNode(x, y, hw, hh, self.depth + 1),            # top left
            QuadtreeNode(x + hw, y, hw, hh, self.depth + 1),       # top right
            QuadtreeNode(x, y + hh, hw, hh, self.depth + 1),       # bottom left
            QuadtreeNode(x + hw, y + hh, hw, hh, self.depth + 1)   # bottom right
        ]

    def _intersects(self, x, y, w, h):
        bx, by, bw, bh = self.bounds
        return not (x > bx + bw or x + w < bx or y > by + bh or y + h < by)
