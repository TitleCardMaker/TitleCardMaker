/**
 * @param {Object} maskArgs Arguments for the mask.
 * @param {HTMLCanvasElement} maskArgs.canvas Canvas element to draw the
 * interactive Mask to.
 * @param {string} maskArgs.imageSource URL to the image of the mask.
 * @param {HTMLButtonElement} maskArgs.applyButton Button whose onclick should
 * apply the path clipping to the mask image.
 * @returns {Function} ...
 */
function initializeEditableMask(maskArgs) {
  const {canvas, imageSource, applyButton} = maskArgs;
  
  // Initialize image which will be drawn to the canas when loaded
  const ctx = canvas.getContext('2d');
  const img = new Image();
  img.src = imageSource;
  img.onload = () => ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

  // Variables to track drawing
  let isDrawing = false;
  const paths = [];

  // Start a new drawing/selection
  canvas.addEventListener('mousedown', (event) => {
    isDrawing = true;
    paths.push([]); // Start a new path
    paths[paths.length - 1].push({ x: event.offsetX, y: event.offsetY });
  });

  // Capture path as mouse is moved
  canvas.addEventListener('mousemove', (event) => {
    // Exit if not in draw mode
    if (!isDrawing) { return; }

    const currentPath = paths[paths.length - 1];
    currentPath.push({ x: event.offsetX, y: event.offsetY });

    // Draw the current path for user feedback
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    ctx.beginPath();
    ctx.setLineDash([5, 5]); // Set dashed line pattern: 5px dash, 5px gap
    for (const path of paths) {
      ctx.moveTo(path[0].x, path[0].y);
      for (let i = 1; i < path.length; i++) {
        ctx.lineTo(path[i].x, path[i].y);
      }
    }
    ctx.strokeStyle = 'white';
    ctx.lineWidth = 2;
    ctx.stroke();
  });

  // Stop drawing
  canvas.addEventListener('mouseup', () => isDrawing = false);
  
  // Helper function to scale coordinates from the main canvas to the offscreen canvas
  function scaleCoordinates(offscreenCanvas, x, y) {
    const scaleX = offscreenCanvas.width / canvas.width;
    const scaleY = offscreenCanvas.height / canvas.height;
    return { x: x * scaleX, y: y * scaleY };
  }

  function clipImageToPaths() {
    // Create an offscreen canvas to render the clipped image
    const offscreenCanvas = document.createElement('canvas');
    offscreenCanvas.width = img.naturalWidth;
    offscreenCanvas.height = img.naturalHeight;
    const offscreenCtx = offscreenCanvas.getContext('2d');

    // Draw the image onto the offscreen canvas
    offscreenCtx.drawImage(img, 0, 0, canvas.width, canvas.height);

    // Set up the clipping paths
    offscreenCtx.globalCompositeOperation = 'destination-in';
    offscreenCtx.beginPath();
    for (const path of paths) {
      offscreenCtx.moveTo(path[0].x, path[0].y);
      for (let i = 1; i < path.length; i++) {
        offscreenCtx.lineTo(path[i].x, path[i].y);
      }
      offscreenCtx.closePath();
    }
    offscreenCtx.fill();

    // Draw the clipped image back onto the main canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(offscreenCanvas, 0, 0);

    // Render clipped image on the offscreen original-width canvas
    const canvas2 = document.createElement('canvas');
    canvas2.width = img.naturalWidth; canvas2.height = img.naturalHeight;
    const ctx2 = canvas2.getContext('2d');
    ctx2.drawImage(img, 0, 0, canvas2.width, canvas2.height);
    ctx2.globalCompositeOperation = 'destination-in';
    ctx2.beginPath();
    for (const path of paths) {
      let coordinates = scaleCoordinates(canvas2, path[0].x, path[0].y);
      ctx2.moveTo(coordinates.x, coordinates.y);

      for (let i = 1; i < path.length; i++) {
        coordinates = scaleCoordinates(canvas2, path[i].x, path[i].y)
        ctx2.lineTo(coordinates.x, coordinates.y);
      }
      ctx2.closePath();
    }
    ctx2.fill();

    return canvas2;
  }

  applyButton.onclick = clipImageToPaths;

  return clipImageToPaths;
}
