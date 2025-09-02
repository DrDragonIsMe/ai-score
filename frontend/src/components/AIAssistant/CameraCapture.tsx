import React, { useRef, useState, useCallback } from 'react';
import { Modal, Button, Space, message } from 'antd';
import { CameraOutlined, CheckOutlined, CloseOutlined, ReloadOutlined } from '@ant-design/icons';

interface CameraCaptureProps {
  visible: boolean;
  onClose: () => void;
  onCapture: (imageData: string) => void;
}

const CameraCapture: React.FC<CameraCaptureProps> = ({ visible, onClose, onCapture }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // 启动相机
  const startCamera = useCallback(async () => {
    try {
      setIsLoading(true);
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'environment' // 优先使用后置摄像头
        }
      });
      
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        videoRef.current.play();
      }
      
      setStream(mediaStream);
      setIsLoading(false);
    } catch (error) {
      console.error('启动相机失败:', error);
      message.error('无法访问相机，请检查权限设置');
      setIsLoading(false);
    }
  }, []);

  // 停止相机
  const stopCamera = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
  }, [stream]);

  // 拍照
  const capturePhoto = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');

    if (!context) return;

    // 设置画布尺寸
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // 绘制视频帧到画布
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // 转换为base64
    const imageData = canvas.toDataURL('image/jpeg', 0.8);
    setCapturedImage(imageData);
  }, []);

  // 重新拍照
  const retakePhoto = useCallback(() => {
    setCapturedImage(null);
  }, []);

  // 确认使用照片
  const confirmPhoto = useCallback(() => {
    if (capturedImage) {
      onCapture(capturedImage);
      handleClose();
    }
  }, [capturedImage, onCapture]);

  // 关闭相机
  const handleClose = useCallback(() => {
    stopCamera();
    setCapturedImage(null);
    onClose();
  }, [stopCamera, onClose]);

  // 当模态框打开时启动相机
  React.useEffect(() => {
    if (visible) {
      startCamera();
    } else {
      stopCamera();
      setCapturedImage(null);
    }
  }, [visible, startCamera, stopCamera]);

  return (
    <Modal
      title="拍照识别题目"
      open={visible}
      onCancel={handleClose}
      footer={null}
      width={800}
      centered
      destroyOnClose
    >
      <div style={{ textAlign: 'center' }}>
        {!capturedImage ? (
          // 相机预览界面
          <div>
            <div style={{ 
              position: 'relative', 
              display: 'inline-block',
              border: '2px solid #d9d9d9',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              <video
                ref={videoRef}
                style={{
                  width: '100%',
                  maxWidth: '640px',
                  height: 'auto',
                  display: 'block'
                }}
                autoPlay
                playsInline
                muted
              />
              
              {/* 拍照指引框 */}
              <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                width: '80%',
                height: '60%',
                border: '2px dashed #1890ff',
                borderRadius: '8px',
                pointerEvents: 'none'
              }}>
                <div style={{
                  position: 'absolute',
                  top: '-30px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  background: 'rgba(24, 144, 255, 0.8)',
                  color: 'white',
                  padding: '4px 12px',
                  borderRadius: '4px',
                  fontSize: '12px'
                }}>
                  请将题目放在框内
                </div>
              </div>
            </div>
            
            <div style={{ marginTop: '16px' }}>
              <Space>
                <Button 
                  type="primary" 
                  icon={<CameraOutlined />} 
                  size="large"
                  onClick={capturePhoto}
                  disabled={isLoading || !stream}
                  loading={isLoading}
                >
                  拍照
                </Button>
                <Button 
                  icon={<CloseOutlined />} 
                  size="large"
                  onClick={handleClose}
                >
                  取消
                </Button>
              </Space>
            </div>
          </div>
        ) : (
          // 照片预览界面
          <div>
            <div style={{ 
              display: 'inline-block',
              border: '2px solid #d9d9d9',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              <img
                src={capturedImage}
                alt="拍摄的照片"
                style={{
                  width: '100%',
                  maxWidth: '640px',
                  height: 'auto',
                  display: 'block'
                }}
              />
            </div>
            
            <div style={{ marginTop: '16px' }}>
              <Space>
                <Button 
                  type="primary" 
                  icon={<CheckOutlined />} 
                  size="large"
                  onClick={confirmPhoto}
                >
                  使用这张照片
                </Button>
                <Button 
                  icon={<ReloadOutlined />} 
                  size="large"
                  onClick={retakePhoto}
                >
                  重新拍照
                </Button>
                <Button 
                  icon={<CloseOutlined />} 
                  size="large"
                  onClick={handleClose}
                >
                  取消
                </Button>
              </Space>
            </div>
          </div>
        )}
        
        {/* 隐藏的画布用于图像处理 */}
        <canvas
          ref={canvasRef}
          style={{ display: 'none' }}
        />
      </div>
    </Modal>
  );
};

export default CameraCapture;