import mesa


class StudentAgent(mesa.Agent):
    def __init__(self, model, path):
        super().__init__(model)  # Mesa 3.x expects the model only
        self.path = list(path)
        self.current_step = 0

    def step(self):
        if self.current_step < len(self.path) - 1:
            self.current_step += 1


class CampusModel(mesa.Model):
    def __init__(self, path):
        super().__init__()
        if not path:
            raise ValueError("A student simulation requires a nonempty route.")
        self.student = StudentAgent(self, path)

    def step(self):
        self.student.step()

    @property
    def finished(self):
        return self.student.current_step >= len(self.student.path) - 1

    @property
    def current_location_id(self):
        return self.student.path[self.student.current_step]
