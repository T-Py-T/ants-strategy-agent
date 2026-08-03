public class Tile {
	Tile(int row, int col) {
		this.row = row;
		this.col = col;
	}

	private final int row;
	private final int col;
	
	public int row() {
		return this.row;
	}
	
	public int col() {
		return this.col;
	}
	
	@Override
	public int hashCode() {
		return this.row * 65536 + this.col;
	}
	
	@Override
	public boolean equals(Object o) {
		return o instanceof Tile
				&& this.row == ((Tile)o).row()
				&& this.col == ((Tile)o).col();
	}
	
	@Override
	public String toString() {
		return "(" + this.row + "," + this.col + ")";
	}
}
