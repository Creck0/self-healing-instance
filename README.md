# Project Self-Heal System

**Title:** AWS-based Self-Healing & Auto Scaling Infrastructure

**Objectives:**
- Build a cloud-based web server architecture with High Availability
- Implement Auto Scaling (automatic scale-out based on CPU utilization)
- Implement Self-Healing (unhealthy instances are automatically replaced)
- Simulate CPU load using `dd` + `gzip` via AWS SSM Agent
- Send automatic admin notifications via Amazon SNS when an alarm triggers

> Supporting files: [`app.py`](./app.py) (Flask + Boto3 backend) and [`templates/index.html`](./templates/index.html) (monitoring dashboard)

---

## Quick Setup

**Stack:** EC2, ALB, Auto Scaling Group, CloudWatch, SNS, Nginx (reverse proxy), Flask + Boto3, region `us-east-1`

1. Launch an EC2 instance (Amazon Linux 2023, t3.micro), install nginx
2. Install python3, flask, boto3 → create `app.py` & `templates/index.html`
3. Create an Image + Launch Template from that instance
4. Create a Target Group + Application Load Balancer (port 80 → target group)
5. Create an Auto Scaling Group (min 2, max 5, target CPU 70%) using the Launch Template, attached to the ALB
6. Create an SNS Topic + email subscription for notifications
7. Create a CloudWatch Alarm: CPUUtilization ≥ 70 → trigger SNS

---

## Testing

1. Run `python3 app.py` on the server, access the dashboard via the Load Balancer DNS (port 5000)
2. Click **"Start Stress Test Now"** → SSM Agent runs `dd | gzip` on all instances to push CPU to 100%

## Expected Results

- CPU spikes sharply, observed in CloudWatch, crossing the 70% threshold
- CloudWatch Alarm switches to **IN ALARM** state
- Auto Scaling Group automatically scales out (new instances appear)
- If an instance becomes unhealthy, the ASG automatically self-heals (replaces it)
- Email notification is automatically sent via SNS when the alarm fires

# Authors
Adhitya Noer Effendi 235150307111024 
Irham Dzaki Alfaruq 235150307111025 
Fadlan Umar Rozikin 235150307111032 
