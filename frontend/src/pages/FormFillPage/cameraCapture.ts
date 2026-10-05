/** Capture the complete native frame: no CSS sizing, crop, or JPEG recompression.
 * The overlay is an aiming aid; it must never cut off a QR's quiet border.
 * This does not sharpen an out-of-focus camera image.
 */
export function captureQrFrame(
  video: HTMLVideoElement,
  canvas: HTMLCanvasElement,
  onBlob: (blob: Blob | null) => void,
): void {
  if (video.readyState < 2 || !video.videoWidth || !video.videoHeight) {
    throw new Error('Camera chưa có hình. Chờ hình rõ rồi bấm chụp lại.');
  }
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const context = canvas.getContext('2d');
  if (!context) throw new Error('Không lấy được ảnh camera. Hãy thử lại.');
  context.drawImage(video, 0, 0);
  canvas.toBlob(onBlob, 'image/png');
}
