from app import db, LCV, app

lcvs = [
        {'id': 1, 'capacity': 4000},
        {'id': 2, 'capacity': 4000},
        {'id': 3, 'capacity': 4000},
        {'id': 4, 'capacity': 4500},
        {'id': 5, 'capacity': 4500},
        {'id': 6, 'capacity': 4000},
        {'id': 7, 'capacity': 4500},
        {'id': 8, 'capacity': 4500},
        {'id': 9, 'capacity': 4000},
        {'id': 10, 'capacity': 5000},
        {'id': 11, 'capacity': 5000},
        {'id': 12, 'capacity': 5000},
        {'id': 13, 'capacity': 5000},
        # Add more LCVs as needed
    ]

with app.app_context():
    db.drop_all()
    db.create_all()

    for lcv_data in lcvs:
        lcv = LCV(id=lcv_data['id'], capacity=lcv_data['capacity'])
        db.session.add(lcv)
        print(f"Adding LCV: {lcv.id}, Capacity: {lcv.capacity}")
    db.session.commit()

    # Verify data
    all_lcvs = LCV.query.all()
    for lcv in all_lcvs:
        print(f"LCV in DB: {lcv.id}, Capacity: {lcv.capacity}")
