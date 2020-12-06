"""abc"""

def sort(collection):
    """abc"""

    note_batch_start_index = 0
    note_batch_range = 3
    type_batch_start_index = 0
    type_batch_range = 2

    note_ids = collection.find_notes("deck:Main::ᏣᎳᎩ")
    #  Get the right notes
    #  set all their indices to 0
    #  Put each note into a liat of dicts with its dependencies' IDs if any

    notes_list = []

    cloze_model = collection.models.get(1607199444709)
    dependency_field = [field for field in cloze_model["flds"] if field["name"] == "Dependencies"][0]
    dependency_field_index = cloze_model["flds"].index(dependency_field)

    for note_id in note_ids:
        note = collection.getNote(note_id)
        dependencies = note.fields[dependency_field_index]
        if dependencies:
            dependencies = dependencies.split("<br>")
        #  get the IDs of the dependencies based on their string
        deps = []
        for dep in dependencies:
            d = collection.find_notes(f"Txt:{dep}")
            if d:
                deps.append(d[0])
        notes_list.append({
            "id": note_id,
            "dependencies": deps
        })
    
    #  Make sure cards are in the correct order based on dependencies
    for note in notes_list:
        note_index = notes_list.index(note)
        highest_dep_index = 0
        for dependency in note["dependencies"]:
            dep_dict = [n for n in notes_list if n["id"] == dependency][0]
            dep_index = notes_list.index(dep_dict)
            if dep_index > highest_dep_index:
                #  have a new highest index
                highest_dep_index = dep_index

        #  if the index of the current note is lower than its highest dependency,
        # or if it's too far away
        if note_index < highest_dep_index or note_index > highest_dep_index + 5:
            #  move the note to be in the next card batch
            new_index = highest_dep_index + note_batch_range
            notes_list.insert(new_index, notes_list.pop(note_index))

    
    #  Sort the cards

    type_sort_order = [
        1, 8, 15, 21, 2, 9, 16, 22, 3, 10, 17, 23, 4, 11, 18, 24, 5, 12, 19, 25, 6, 13, 20, 26, 7, 14
    ]

    index = 0
    note_dicts = True

    while note_dicts:
        # Get a batch of 5 notes
        note_dicts = notes_list[
            note_batch_start_index:note_batch_start_index + note_batch_range
        ]

        type_batch = True
        while type_batch:
            # Get a batch of 3 types
            type_batch = type_sort_order[
                type_batch_start_index:type_batch_start_index + type_batch_range
            ]
            # For each of the 5 cards, set the due for its types
            for card_type in type_batch:
                for note_dict in note_dicts:
                    note = collection.getNote(note_dict["id"])
                    note_card_ids = collection.find_cards(f"nid:{note.id}")
                    note_cards = [
                        collection.getCard(cid)
                    for cid in note_card_ids]

                    try:
                        card = [x for x in note_cards if x.ord == card_type - 1][0]
                        card.due = index + 1
                        index += 1
                        card.flush()
                    except IndexError:
                        # This note doesn't have this card type
                        pass

            type_batch_start_index += type_batch_range
        
        type_batch_start_index = 0
        note_batch_start_index += note_batch_range

    pass
            


    #  For each note,
    #  if it has dependencies
    #  get the indices of each dependency
    #  if the index of the current note is lower than its highest dependency,
    #  move the note to be 2 ahead of its highest
    #  loop this until we do a loop where nothing is moved due to dependencies

    #  The order we want for any given note is:

    #  1
    #  8
    #  15
    #  21
    #  2
    #  9
    #  16
    #  22
    #  3
    #  10
    #  17
    #  23
    #  4
    #  11
    #  18
    #  24
    #  5
    #  12
    #  19
    #  25
    #  6
    #  13
    #  20
    #  26
    #  7
    #  14
    #  27

    #  we will do the first 3 cards for the first 5 notes,
    #  then do the next 3 cards for the first 5 notes,
    #  and so on, until we run out of cards
    #  then we start from the first card again, with the next lot of 5 notes
    #  and repeat until we've done all the notes

    #  If the note doesn't have that particular card (cloze deletion) then we just skip it