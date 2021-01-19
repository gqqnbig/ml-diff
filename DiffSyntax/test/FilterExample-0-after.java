 	 *	image is a rectangular matrix, neighberhoodSize > 0
 	 *post: return a smoothed version of image
 	 */
	public Color[][] smoothIt(Color[][] image, int neighberhoodSize)
 	{	//check precondition
 		assert image != null && image.length > 1 && image[0].length > 1
 				&& ( neighberhoodSize > 0 ) && rectangularMatrix( image )
