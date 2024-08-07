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

    valid: bool = True
    warnings: list[str] = []

    # Get the townhall building
    townhall: dict | None = None
    previous_townhall: dict | None = None
    current_buildings: dict = {}
    positions = []

    for building in buildings:
        building_name: str = building.get("name")
        building_level: int = int(building.get("level"))

        if building_name == 'townhall':
            townhall = building
        
            if 'townhall' in building_cache and building_level > 1:
                previous_townhall = building_cache['townhall'][str(building_level - 1)]
            
        if building_name not in current_buildings:
            current_buildings[building_name] = [building_level]
        else:
            current_buildings[building_name].append(building_level)
        
        if not building.get('positions') in positions:
            positions.append(building.get('positions'))
        else:
            warnings.append(f"Building {building_name} is overlapping with another building")
            valid = False
    
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
    max_combined_count: dict = {}
    for d in [max_resources_count, max_army_count, max_defense_count, max_trap_count]:
        for key, value in d.items():
            max_combined_count[key] = max_combined_count.get(key, 0) + value
    
    max_combined_level: dict = {}
    for d in [max_resources_level, max_army_level, max_defense_level, max_trap_level]:
        for key, value in d.items():
            max_combined_level[key] = max_combined_level.get(key, 0) + value
    
    for building_name in current_buildings:
        if building_name not in max_combined_count.keys() and building_name != 'townhall':
            warnings.append(f"Building {building_name} not found in townhall")
            valid = False
        
        if max_combined_count.get(building_name) is None:
            if building_name != 'townhall':
                warnings.append(f"Building {building_name} count not found")
            continue
        
        # Check the count
        if len(current_buildings.get(building_name)) > max_combined_count.get(building_name):
            warnings.append(f"Building {building_name} count is more than allowed")
            valid = False

        # Check the level
        if max_combined_level.get(building_name) is None:
            warnings.append(f"Building {building_name} level not found")
            continue

        if max(current_buildings.get(building_name)) > max_combined_level.get(building_name):
            warnings.append(f"Building {building_name} level is more than allowed")
            valid = False
        
    if previous_townhall is None:
        for warning in warnings:
            print(f'[!] {warning}')
        return valid
    
    min_resources_count: dict = previous_townhall.get('max number of resource')
    min_army_count: dict = previous_townhall.get('max number of army')
    min_defense_count: dict = previous_townhall.get('max number of defense')
    min_trap_count: dict = previous_townhall.get('max number of traps')

    # Combine the dictionaries
    min_combined_count: dict = {}
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


def generate_structures_list(buildings: list[dict], building_cache: dict, cell_size: int) -> list[dict]:
    """
    Generate the structures from the buildings in the village

    :param buildings: The list of buildings in the village
    :param building_cache: The cache of building data
    :param cell_size: The size of each cell in the grid
    :return list[dict]: The list of structures
    """

    structures: list[dict] = []

    for building in buildings:
        building_name: str = building.get("type")
        building_level: str = str(building.get("level"))

        if building_name not in building_cache:
            building_data: dict = json.load(open(f".{os.sep}data{os.sep}structures{os.sep}{building_name.replace(' ', '_')}.json"))
            building_cache[building_name] = building_data

        building_size: dict = building_cache[building_name].get("size")
        building_inset: float = building_cache[building_name].get("inset")
        building_type: str = building_cache[building_name].get("type")

        # Check if the building has only one position, if so then make a list of one position
        if building_cache[building_name].get("max count") == 1:
            building_positions: list[list[int]] = [[building.get("x"), building.get("y")]]
        else:
            building_positions: list[list[int]] = building.get('positions')


        for position in building_positions:
            structure: dict = copy.deepcopy(building_cache[building_name][building_level])

            # WAY more optimized to generate center once, rather than every frame
            # Calculate the center position of the structure
            center_x: int = (position[0] + building_size.get('width') // 2) * cell_size
            center_y: int = (position[1] + building_size.get('height') // 2) * cell_size

            # Adjust center position for odd-sized structures
            if building_size.get('width') % 2 != 0:
                center_x += cell_size // 2
            if building_size.get('height') % 2 != 0:
                center_y += cell_size // 2

            structure.update({
                'level': building_level,
                'name': building_name,
                'type': building_type,
                'position': position,
                'center': [center_x, center_y],
                'size': building_size,
                'inset': building_inset
            })
            
            if building_name == 'army camp':
                structure['troops'] = building.get('troops')

            structures.append(structure)

    return structures


def draw_grid(window: pygame.surface, cell_size: int, num_rows: int, num_cols: int) -> None:
    """
    Draw the grid on the window

    :param window: The window to draw the grid on
    :param cell_size: The size of each cell in the grid
    :param num_rows: The number of rows in the grid
    :param num_cols: The number of columns in the grid
    :return None:
    """

    # Clear the window
    window.fill((255, 255, 255))

    for row in range(num_rows):
        for col in range(num_cols):
            pygame.draw.rect(window, (0, 0, 0), (col * cell_size, row * cell_size, cell_size, cell_size), 1)


def draw_structures(window: pygame.surface, cell_size: int, structures: list[dict], building_colors: dict) -> None:
    """
    Draw the structures on the window

    :param window: The window to draw the structures on
    :param cell_size: The size of each cell in the grid
    :param structures: The list of structures to draw
    :param building_colors: The colors of the buildings
    :return None:
    """

    for structure in structures:
        position: list[int] = structure.get("position")
        size: dict = structure.get("size")
        center: list[int] = structure.get("center")

        # Draw the structure
        for row in range(size.get('width')):
            for col in range(size.get('height')):
                x: int = (position[0] + col) * cell_size
                y: int = (position[1] + row) * cell_size

                # Use building color
                if structure.get('name') in building_colors:
                    pygame.draw.rect(window, building_colors[structure.get('name')], (x, y, cell_size, cell_size))
                else:
                    pygame.draw.rect(window, (0, 0, 0), (x, y, cell_size, cell_size))

        # Draw level in the middle
        level: int = structure.get('level')
        font: pygame.font = pygame.font.Font(None, 20)
        text = font.render(str(level), True, (0, 0, 0))
        text_rect = text.get_rect(center=(center[0], center[1]))
        window.blit(text, text_rect)


def main(cell_size: int, num_rows: int, num_cols: int, fps: int, village: dict, building_colors: dict) -> None:
    """
    The main function of the program

    :param cell_size: The size of each cell in the grid
    :param num_rows: The number of rows in the grid
    :param num_cols: The number of columns in the grid
    :param village: The village data
    :param building_colors: The colors of the buildings
    :return None:
    """
    
    if village is None:
        print("No village data found")
        return None

    pygame.init()

    window_width: int = num_cols * cell_size
    window_height: int = num_rows * cell_size

    window: pygame.surface = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("Grid Window")

    clock: pygame.time.Clock = pygame.time.Clock()
    
    buildings: list[dict] | list = village.get("buildings", [])
    building_cache: dict = {}
    
    structures: list[dict] = generate_structures_list(buildings, building_cache, cell_size)
    valide_villate: bool = validate_village(structures, building_cache)

    if not valide_villate:
        print("Invalid village")
    else:
        print("Valid village")

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

        draw_grid(window, cell_size, num_rows, num_cols)
        draw_structures(window, cell_size, structures, building_colors)
                    
        # Update the display
        pygame.display.flip()

        # Limit the frame rate
        clock.tick(fps)


if __name__ == "__main__":
    # Load the configuration file
    with open(f".{os.sep}data{os.sep}config.json") as file:
        config = json.load(file)
    
    # Extract the configuration values
    cell_size: int = config.get("cell_size", 10)
    num_rows: int = config.get("rows", 44)
    num_cols: int = config.get("cols", 44)
    building_colors: dict = config.get("building_colors", {})
    village: dict | None = None

    # Parse the command line arguments
    parser = argparse.ArgumentParser()

    parser.add_argument("--cell_size", type=int, default=cell_size)
    parser.add_argument("--num_rows", type=int, default=num_rows)
    parser.add_argument("--num_cols", type=int, default=num_cols)
    parser.add_argument("--fps", type=int, default=60)
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
    main(cell_size, num_rows, num_cols, args.fps, village, building_colors)
    pygame.quit()
