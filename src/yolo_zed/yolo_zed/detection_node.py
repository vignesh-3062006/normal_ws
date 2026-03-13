import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from zed_interfaces.msg import ObjectsStamped
from cv_bridge import CvBridge
import cv2
import message_filters

class ZedDetectionOverlay(Node):
    def __init__(self):
        super().__init__('zed_detection_overlay')
        self.bridge = CvBridge()
        
        # 1. Setup Subscribers for Synchronization
        self.image_sub = message_filters.Subscriber(self, Image, '/zed/zed_node/left/image_rect_color')
        self.obj_sub = message_filters.Subscriber(self, ObjectsStamped, '/zed/zed_node/obj_det/objects')

        # 2. ApproximateTimeSynchronizer (slop=0.1 means 100ms max difference)
        self.ts = message_filters.ApproximateTimeSynchronizer(
            [self.image_sub, self.obj_sub], queue_size=10, slop=0.1
        )
        self.ts.registerCallback(self.callback)

        # 3. Setup Publisher for the result
        self.publisher = self.create_publisher(Image, '/zed/obj_det_annotated', 10)
        self.get_logger().info("ZED Overlay Node Started! View /zed/obj_det_annotated in RViz.")

    def callback(self, img_msg, obj_msg):
        # Convert ROS Image to OpenCV format
        cv_image = self.bridge.imgmsg_to_cv2(img_msg, "bgr8")

        # Loop through detected objects
        for obj in obj_msg.objects:
            # ZED uses 2D corners for the bounding box
            # 0 ------- 1
            # |         |
            # 3 ------- 2
            top_left = obj.bounding_box_2d.corners[0]
            bottom_right = obj.bounding_box_2d.corners[2]

            x1, y1 = int(top_left.kp[0]), int(top_left.kp[1])
            x2, y2 = int(bottom_right.kp[0]), int(bottom_right.kp[1])

            # Draw rectangle and label
            label = f"{obj.label} ({int(obj.confidence)}%)"
            cv2.rectangle(cv_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(cv_image, label, (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Convert back to ROS message and publish
        out_msg = self.bridge.cv2_to_imgmsg(cv_image, "bgr8")
        out_msg.header = img_msg.header # Keep the timestamp
        self.publisher.publish(out_msg)

def main(args=None):
    rclpy.init(args=args)
    node = ZedDetectionOverlay()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()