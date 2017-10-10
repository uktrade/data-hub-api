from model_utils import Choices


PaymentMethod = Choices(
    ('card', 'Card'),
    ('bacs', 'BACS'),
    ('cheque', 'Cheque'),
    ('manual', 'Manual'),
)
