#include <micro_ros_arduino.h>

#include <rcl/rcl.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>

#include <geometry_msgs/msg/twist.h>

// ----------- Robot Parameters -----------
#define WHEEL_RADIUS 0.07      // meters
#define BASE_WIDTH   0.68      // distance between wheels (meters)

// ----------- Motor Pins -----------
#define LEFT_PWM  23
#define LEFT_DIR  19
#define RIGHT_PWM 22
#define RIGHT_DIR 21

// ----------- micro-ROS -----------
rcl_subscription_t subscriber;
geometry_msgs__msg__Twist msg;

rclc_executor_t executor;
rcl_node_t node;
rcl_allocator_t allocator;
rclc_support_t support;

// ----------- Motor Control Function -----------
void set_motor(int pwm_pin, int dir_pin, float speed)
{
  int direction = (speed >= 0) ? HIGH : LOW;
  float pwm = fabs(speed);

  if (pwm > 50) pwm = 50;

  digitalWrite(dir_pin, direction);
  analogWrite(pwm_pin, (int)pwm);
}

// ----------- cmd_vel Callback -----------
void cmd_vel_callback(const void * msgin)
{
  const geometry_msgs__msg__Twist * cmd =
      (const geometry_msgs__msg__Twist *)msgin;

  float v = cmd->linear.x;   // m/s
  float w = cmd->angular.z;  // rad/s

  // Differential drive kinematics
  float v_left  = (v - (w * BASE_WIDTH / 2.0)) / WHEEL_RADIUS;
  float v_right = (v + (w * BASE_WIDTH / 2.0)) / WHEEL_RADIUS;

  // Convert to PWM scale
  float scale = 30.0;

  int pwm_left  = v_left * scale;
  int pwm_right = v_right * scale;

  set_motor(LEFT_PWM, LEFT_DIR, pwm_left);
  set_motor(RIGHT_PWM, RIGHT_DIR, pwm_right);
}

// ----------- Setup -----------
void setup()
{
  set_microros_transports();
  delay(2000);  // allow agent to connect

  // 🔥 TIME SYNC (CRITICAL)
  rmw_uros_sync_session(1000);

  // Motor pins
  pinMode(LEFT_PWM, OUTPUT);
  pinMode(LEFT_DIR, OUTPUT);
  pinMode(RIGHT_PWM, OUTPUT);
  pinMode(RIGHT_DIR, OUTPUT);

  allocator = rcl_get_default_allocator();

  // Create support
  rclc_support_init(&support, 0, NULL, &allocator);

  // Create node
  rclc_node_init_default(&node, "diff_drive_node", "", &support);

  // Create subscriber
  rclc_subscription_init_default(
    &subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist),
    "/cmd_vel"
  );

  // Create executor
  rclc_executor_init(&executor, &support.context, 1, &allocator);

  rclc_executor_add_subscription(
    &executor,
    &subscriber,
    &msg,
    &cmd_vel_callback,
    ON_NEW_DATA
  );
}

// ----------- Loop -----------

void loop()
{
    rclc_executor_spin_some(&executor, RCL_MS_TO_NS(100));
}