from cubedata import RichCubeData as CubeData
import sys

if __name__ == "__main__":
    cube_data = CubeData(draft_size=90)
    cube_data.read_cube_csv(sys.argv[1])
    cube_data.start_game()
