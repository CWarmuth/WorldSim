class TerrainTile:
    def __init__(self, x: int, y: int, width: int, height: int, surface: str, color, plate_index: int = None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.plate_index = plate_index
        self.surface = surface
        self.color = color
        self.highlight = False

    def __copy__(self):
        tile = TerrainTile(self.x, self.y, self.width, self.height, self.surface, self.color, self.plate_index)
        tile.highlight = self.highlight
        return tile

    def __str__(self):
        return f"TerrainTile at ({self.x}, {self.y}) terrain of type {self.surface}"


class Rectangle:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class QuadTree:
    def __init__(self, bounds):
        self.bounds = bounds
        self.nodes = None
        self.rectangles = []

    def get_rectangles(self):
        plate_indices = self.rectangles

        if self.nodes:
            for node in self.nodes:
                plate_indices.extend(node.get_rectangles())
        return plate_indices

    # def get_overlap_results(self):
    #     plate_indices = []
    #     for rect in self.rectangles:
    #         plate_indices.append(self.is_colliding(rect))
    #     return plate_indices

    def insert(self, rectangle):
        rect, plate_index = rectangle
        if self.nodes is not None:
            index = self.get_index(rect)
            if index != -1:
                self.nodes[index].insert(rectangle)
                # print(f"inserting into child at {rect.x} {rect.y}")
                return
        self.rectangles.append(rectangle)
        # print(f"inserted {rect.x} {rect.y}")
        if len(self.rectangles) > 20:
            self.split()

    def split(self):
        if self.nodes is None:
            x = self.bounds.x
            y = self.bounds.y
            width = self.bounds.WIDTH
            height = self.bounds.HEIGHT

            half_width = width // 2
            half_height = height // 2

            self.nodes = list({
                QuadTree(
                    Rectangle(x, y, half_width, half_height),
                ),
                QuadTree(
                    Rectangle(x + half_width, y, half_width, half_height)
                ),
                QuadTree(
                    Rectangle(x, y + half_height, half_width, half_height)
                ),
                QuadTree(
                    Rectangle(x + half_width, y + half_height, half_width, half_height)
                )
            })

        i = 0
        while i < len(self.rectangles):
            rect, _ = self.rectangles[i]
            index = self.get_index(rect)
            if index != -1:
                # print(f"Pixel at {rect.x} {rect.y} moved into child node. Child now has size {self.nodes[index]}")
                self.nodes[index].insert(self.rectangles.pop(i))
                continue
            i += 1

    def move_rectangles(self, plates):
        # Move the rectangles stored in this node
        for rect, plate_index in self.rectangles:
            direction = plates[plate_index].direction
            new_x = rect.x + direction[0]
            new_y = rect.y + direction[1]
            self.move_rectangle((rect, plate_index), new_x, new_y)

        # Move the rectangles stored in the child nodes
        if self.nodes:
            for node in self.nodes:
                node.move_rectangles(plates)

    def move_rectangle(self, rectangle, new_x, new_y):
        rect, plate_index = rectangle
        # Remove the rectangle from its current position in the quadtree
        self.rectangles = [r for r in self.rectangles if r[0] != rectangle[0]]
        if self.nodes:
            for node in self.nodes:
                node.rectangles = [r for r in node.rectangles if r[0] != rectangle[0]]

        # Update the rectangle's position
        rect.x = new_x
        rect.y = new_y

        # Insert the rectangle into the quadtree at its new position
        self.insert(rectangle)

    def get_index(self, rectangle):
        is_inside_bounds = rectangle.x > self.bounds.x and rectangle.y > self.bounds.y and \
                           rectangle.x + rectangle.WIDTH < self.bounds.x + self.bounds.WIDTH and \
                           rectangle.y + rectangle.HEIGHT < self.bounds.y + self.bounds.HEIGHT
        if not is_inside_bounds:
            return -1
        is_top_quadrant = (rectangle.y + rectangle.HEIGHT) < self.bounds.y + self.bounds.HEIGHT / 2
        is_bottom_quadrant = rectangle.y > self.bounds.y + self.bounds.HEIGHT / 2
        is_left_quadrant = (rectangle.x + rectangle.WIDTH) < self.bounds.x + self.bounds.WIDTH / 2
        is_right_quadrant = rectangle.x > self.bounds.x + self.bounds.WIDTH / 2

        if is_left_quadrant and is_top_quadrant:
            # top left
            return 0
        elif is_right_quadrant and is_top_quadrant:
            # top right
            return 1
        elif is_left_quadrant and is_bottom_quadrant:
            # bottom left
            return 2
        elif is_right_quadrant and is_bottom_quadrant:
            # bottom right
            return 3

        # rectangle cannot completely fit within a child quadrant, so it must be partially contained
        # in this quadrant
        return -1

    def is_out_of_bounds(self, rectangle):
        return not self.rectangles_overlap(rectangle, self.bounds)

    def is_colliding(self, rectangle):
        rect, _ = rectangle
        # check if the rectangle is colliding with any of the rectangles in this quad
        for r, i in self.rectangles:
            if self.rectangles_overlap(r, rect):
                return True
        # check if the rectangle is colliding with any of the rectangles in the child quads
        for node in self.nodes:
            if node is not None and node.is_colliding(rectangle):
                return True
        return False

    @staticmethod
    def rectangles_overlap(rect1, rect2):
        # Check if the x-coordinates of the rectangles overlap
        x_overlap = rect1.x <= rect2.x + rect2.WIDTH and rect2.x <= rect1.x + rect1.WIDTH
        # Check if the y-coordinates of the rectangles overlap
        y_overlap = rect1.y <= rect2.y + rect2.HEIGHT and rect2.y <= rect1.y + rect1.HEIGHT
        # Return true if both x and y overlap, false otherwise
        return x_overlap and y_overlap


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
