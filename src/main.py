import os
import copy
import json
import pygame
import argparse


def validate_village(buildings: list[dict], building_cache: dict) -> bool:
    """
    Validate the village data

    :param buildings: The list of buildings in the village
    :param building_cache: The cache of building data
    :return bool: True if the village is valid, False otherwise
    """

    valid = True
    warnings: list[str] = []

    # Get the townhall building
    townhall = None
    previous_townhall = None
    current_buildings = {}

    for building in buildings:
        building_type: str = building.get("type")
        building_level: int = int(building.get("level"))

        if building_type == 'townhall':
            townhall = building
        
            if 'townhall' in building_cache and building_level > 1:
                previous_townhall: dict = building_cache['townhall'][str(building_level - 1)]
            
        if building_type not in current_buildings:
            current_buildings[building_type] = [building_level]
        else:
            current_buildings[building_type].append(building_level)
    
    if townhall is None:
        print("No townhall found, unable to validate village!")
        return False
    
    max_resources_count: dict = townhall.get('max number of resource')
    max_resources_level: dict = townhall.get('max level of resource')
    max_army_count: dict = townhall.get('max number of army')
    max_army_level: dict = townhall.get('max level of army')
    max_defense_count: dict = townhall.get('max number of defense')
    max_defense_level: dict = townhall.get('max level of defense')
    max_trap_count: dict = townhall.get('max number of traps')
    max_trap_level: dict = townhall.get('max level of traps')

    # Combine the dictionaries
    max_combined_count = {}
    for d in [max_resources_count, max_army_count, max_defense_count, max_trap_count]:
        for key, value in d.items():
            max_combined_count[key] = max_combined_count.get(key, 0) + value
    
    max_combined_level = {}
    for d in [max_resources_level, max_army_level, max_defense_level, max_trap_level]:
        for key, value in d.items():
            max_combined_level[key] = max_combined_level.get(key, 0) + value
    
    
    for building_type in current_buildings:
        if building_type not in max_combined_count.keys() and building_type != 'townhall':
            warnings.append(f"Building {building_type} not found in townhall")
            valid = False
        
        if max_combined_count.get(building_type) is None:
            if building_type != 'townhall':
                warnings.append(f"Building {building_type} count not found")
            continue
        
        # Check the count
        if len(current_buildings.get(building_type)) > max_combined_count.get(building_type):
            warnings.append(f"Building {building_type} count is more than allowed")
            valid = False

        # Check the level
        if max_combined_level.get(building_type) is None:
            warnings.append(f"Building {building_type} level not found")
            continue

        if max(current_buildings.get(building_type)) > max_combined_level.get(building_type):
            warnings.append(f"Building {building_type} level is more than allowed")
            valid = False
        
    if previous_townhall is None:
        for warning in warnings:
            print(f'[!] {warning}')
        return valid
    
    min_resources_count = previous_townhall.get('max number of resource')
    min_army_count = previous_townhall.get('max number of army')
    min_defense_count = previous_townhall.get('max number of defense')
    min_trap_count = previous_townhall.get('max number of traps')

    # Combine the dictionaries
    min_combined_count = {}
    for d in [min_resources_count, min_army_count, min_defense_count, min_trap_count]:
        for key, value in d.items():
            min_combined_count[key] = min_combined_count.get(key, 0) + value


    for min_building in min_combined_count.keys():
        if min_building not in current_buildings:
            warnings.append(f"Building {min_building} not found")
            valid = False
            continue

        if min_combined_count.get(min_building) > len(current_buildings.get(min_building)):
            warnings.append(f"Building {min_building} count is less than required")
            valid = False
    
    for warning in warnings:
        print(f'[!] {warning}')

    return valid


def generate_sctructure_list(buildings: list[dict], building_cache: dict) -> list[dict]:
    """
    Generate the structures from the buildings in the village

    :param buildings: The list of buildings in the village
    :param building_cache: The cache of building data
    :return list[dict]: The list of structures
    """

    structures = []

    for building in buildings:
        building_type: str = building.get("type")
        building_level: str = str(building.get("level"))

        if building_type not in building_cache:
            building_data: dict = json.load(open(f".{os.sep}data{os.sep}structures{os.sep}{building_type.replace(' ', '_')}.json"))
            building_cache[building_type] = building_data

        building_size: dict = building_cache[building_type].get("size")

        if building_cache[building_type].get("max count") == 1:
            structure: dict = building_cache[building_type][building_level]
            structure['level'] = building_level
            structure['type'] = building_type
            structure['position'] = [building.get("x"), building.get("y")]
            structure['size'] = building_size

            structures.append(structure)
            
        else:
            building_position: list[list[int]] = building.get('positions')
            for position in building_position:
                structure: dict = copy.deepcopy(building_cache[building_type][building_level])
                structure['level'] = building_level
                structure['type'] = building_type
                structure['position'] = position
                structure['size'] = building_size

                structures.append(structure)

    return structures


def main(cell_size: int, num_rows: int, num_cols: int, village: dict, building_colors: dict) -> None:
    """
    The main function of the program

    :param cell_size: The size of each cell in the grid
    :param num_rows: The number of rows in the grid
    :param num_cols: The number of columns in the grid
    :param village: The village data
    :param building_colors: The colors of the buildings
    :return None:
    """
    pygame.init()

    window_width = num_cols * cell_size
    window_height = num_rows * cell_size

    window = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("Grid Window")


    if village is None:
        return
    
    buildings: list[dict] | list = village.get("buildings", [])
    building_cache: dict = {}
    
    structures: list[dict] = generate_sctructure_list(buildings, building_cache)
    valide_villate: bool = validate_village(structures, building_cache)

    if not valide_villate:
        print("Invalid village")
    else:
        print("Valid village")


    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

        # Clear the window
        window.fill((255, 255, 255))

        # Draw the grid
        for row in range(num_rows):
            for col in range(num_cols):
                pygame.draw.rect(window, (0, 0, 0), (col * cell_size, row * cell_size, cell_size, cell_size), 1)
        
        # Draw the structures
        for structure in structures:
            position = structure.get("position")
            size = structure.get("size")

            for row in range(size.get('width')):
                for col in range(size.get('height')):
                    x = (position[0] + col) * cell_size
                    y = (position[1] + row) * cell_size

                    #use building color
                    if structure.get('type') in building_colors:
                        pygame.draw.rect(window, building_colors[structure.get('type')], (x, y, cell_size, cell_size))
                    else:
                        pygame.draw.rect(window, (0, 0, 0), (x, y, cell_size, cell_size))
                    
        # Update the display
        pygame.display.flip()


if __name__ == "__main__":
    # Load the configuration file
    with open(f".{os.sep}data{os.sep}config.json") as file:
        config = json.load(file)
    
    # Extract the configuration values
    cell_size: int = config.get("cell_size", 10)
    num_rows: int = config.get("num_rows", 44)
    num_cols: int = config.get("num_cols", 44)
    building_colors: dict = config.get("building_colors", {})
    village = None

    # Parse the command line arguments
    parser = argparse.ArgumentParser()

    parser.add_argument("--cell_size", type=int, default=cell_size)
    parser.add_argument("--num_rows", type=int, default=num_rows)
    parser.add_argument("--num_cols", type=int, default=num_cols)
    parser.add_argument("--input_village", type=str, default=None)

    args = parser.parse_args()

    if args.cell_size:
        cell_size = args.cell_size
    
    if args.num_rows:
        num_rows = args.num_rows
    
    if args.num_cols:
        num_cols = args.num_cols
    
    if args.input_village:
        print(f"Loading village from {args.input_village}")

        with open(args.input_village) as file:
            village: dict = json.load(file)

    # Run the main function
    main(cell_size, num_rows, num_cols, village, building_colors)
    pygame.quit()
