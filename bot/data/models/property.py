# bot\data\models\property.py

class Property:
    def __init__(self, id, type, street, home, flat, price, pricem, 
                 floor, floors_total, status, photo, photocnt, homeid, creation_date):
        self.id = id
        self.type = type
        self.street = street
        self.home = home
        self.flat = flat
        self.price = price
        self.pricem = pricem
        self.floor = floor
        self.floors_total = floors_total
        self.status = status
        self.photo = photo
        self.photocnt = photocnt
        self.homeid = homeid
        self.creation_date = creation_date