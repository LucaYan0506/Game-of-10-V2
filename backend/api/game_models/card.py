class Card:
    '''
    the number/operators that players place down
    '''
    def __init__(self, i, j, val, id):
        self.i: int = i
        self.j: int = j
        self.val: str = val
        self.id: int = id

    def __str__(self):
        return f"\n      {self.val} at i={self.i} j={self.j}"

    __repr__ = __str__

    def __hash__(self):
        return hash((self.i, self.j, self.val))

    def __eq__(self, other):
        return isinstance(other, Card) and (self.i, self.j, self.val) == (other.i, other.j, other.val)
