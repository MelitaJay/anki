from datetime import datetime

note_count = 2
batch_count = 3
card_count = 3

def sort_notes_by_dependencies(collection):

    """
        Sort the notes by their dependencies.
        This means that if a card is dependent on another,
        that other card will appear first.
    """

    note_ids = collection.find_notes("deck:Main::ᏣᎳᎩ")
    # note_ids = collection.find_notes("deck:Main::Svenska 🇸🇪")

    #  Get the right notes
    #  set all their indices to 0
    #  Put each note into a list of dicts with its dependencies' IDs if any
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
            dep_value = collection.find_notes(f"Txt:{dep}")
            if dep_value:
                deps.append(dep_value[0])
        notes_list.append({
            "id": note_id,
            "dependencies": deps
        })

    new_notes_list = notes_list.copy()
    
    #  Make sure notes are in the correct order based on dependencies
    for note in notes_list:
        note_index = notes_list.index(note)
        highest_dep_index = 0
        for dependency in note["dependencies"]:
            # Get the index of the dependency
            dep_dict = [n for n in notes_list if n["id"] == dependency][0]
            dep_index = notes_list.index(dep_dict)
            if dep_index > highest_dep_index:
                # have a new highest index
                highest_dep_index = dep_index

        # if the index of the notes is such that the dependency is in the same group, move the dependent to the next group
        min_requirement = highest_dep_index + (note_count * batch_count * card_count)
        if highest_dep_index and note_index < min_requirement:
            # move the note to be in the next group
            new_index = min_requirement
        else:
            new_index = notes_list.index(note)

        new_notes_list.insert(new_index, new_notes_list.pop(note_index))
            
    # We now know what order the notes should be in
    return new_notes_list

def sort_cards(notes_list, collection):

    '''
    e.g.
    if 
        note_count = 3
        card_count = 2
        batch_count = 4

        We get the first batch of 3 notes
        For these notes, we get the first 2 cards
        Then we move on to the next 3 notes, and do the same
        Then the next 3 notes
        And another 3

        We have 4 batches of 3 notes - this is a group (12 notes),
        Then we go back to the first 3 notes of this group, and do the next 2 cards
        and so on, until we get to the end of the 4 batches of 3s (the group)

        After we've done all the cards for this group, we start again with another group.
        
        This will mean that we're not introducing too many different notes at once,
        or too many cards for the same note.

    '''

    # This is the order we want our cards to appear in for a given note
    card_sort_order = [
        # 1, 8, 15, 21, 2, 9, 16, 22, 3, 10, 17, 23, 4, 11, 18, 24, 5, 12, 19, 25, 6, 13, 20, 26, 7, 14
        21, 22, 23, 24, 25, 26, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
    ]

    # First, split the notes into batches
    batches = []
    x = 0
    while x < len(notes_list):
        notes_for_batch = notes_list[x:x+note_count]
        batches.append(notes_for_batch)
        x += note_count

    # Then add them to groups
    groups = []
    y = 0
    while y < len(batches):
        batches_for_group = batches[y:y+batch_count]
        groups.append(batches_for_group)
        y += batch_count

    # Then process the groups, one at a time

    group_index = 0

    master_index = 1

    for group in groups:

        # Set everything to zero for the new group
        note_index = 0
        card_index = 0
        card_tracker = 0

        while card_tracker < len(card_sort_order):

            # We're going to the start of the group
            batch_index = 0

            while batch_index < batch_count:
                try:
                    batch = group[batch_index]
                except IndexError:
                    break
                while note_index < note_count:
                    try:
                        _ = batch[note_index]
                    except IndexError:
                        break
                    while card_index < card_count:

                        desired_card_index = card_tracker + card_index

                        note_id = group[batch_index][note_index]["id"]

                        # note = collection.getNote(note_id)
                        # note.fields[15] = 'all,1,all | n,n,n,n'
                        # note.flush()

                        cards_for_note = [
                            collection.getCard(cid)
                        for cid in collection.find_cards(f"nid:{note_id}")]
                        
                        try:
                            # card_id = collection.find_cards(f"nid:{note_id}")[card_tracker]
                            # card = collection.getCard(card_id)
                            card = [x for x in cards_for_note if x.ord + 1 == card_sort_order[desired_card_index]][0]
                            # If the card's not got a proper due set (aka we're alredy studying it)
                            if datetime.now() > datetime.fromtimestamp(card.due):
                                card.due = master_index
                                card.flush()
                                master_index += 1
                            if group_index == 0:
                                print(group_index, batch_index, note_index, card_tracker, desired_card_index, master_index)
                        except IndexError:
                            # print("NO CARD")
                            # This note doesn't have this card type
                            pass

                        card_index += 1

                    card_index = 0
                    note_index += 1

                note_index = 0
                batch_index += 1

            card_tracker += card_count
            # We're going over the group again for the next lot of cards
            if group_index == 0:
                print("RESTARTING GROUP")

        if group_index == 0:
            print("DONE WITH GROUP")
        group_index += 1

    print("DONE")

def sort(collection):
    """Perform the sort"""

    notes_list = sort_notes_by_dependencies(collection)

    sort_cards(notes_list, collection)
