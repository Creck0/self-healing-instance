#!/usr/bin/python
import boto3
from flask import Flask, flash, redirect, render_template, url_for, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "super_secret_key_chaos_lab"

# Konfigurasi AWS Client
AWS_REGION = "us-east-1"
ec2_client = boto3.client("ec2", region_name=AWS_REGION)
ssm_client = boto3.client("ssm", region_name=AWS_REGION)
cloudwatch_client = boto3.client("cloudwatch", region_name=AWS_REGION)

# NAMA ASG ANDA (Pastikan nama ini sesuai dengan di AWS Console)
ASG_NAME = "Your-name-ASG"


def get_active_instances():
    """Mencari Instance ID yang berstatus 'running' di dalam ASG terkait"""
    try:
        response = ec2_client.describe_instances(
            Filters=[
                {"Name": "tag:aws:autoscaling:groupName", "Values": [ASG_NAME]},
                {"Name": "instance-state-name", "Values": ["running"]},
            ]
        )
        instance_ids = []
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                instance_ids.append(instance["InstanceId"])
        return instance_ids
    except Exception as e:
        print(f"Error mendeteksi instance: {e}")
        return []


@app.route("/")
def index():
    return render_template("index.html")


# API UNTUK ALL INSTANCES
@app.route("/api/cpu-data")
def cpu_data():
    instances = get_active_instances()
    chart_data = {}

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=10)

    # Kumpulkan semua data server dulu baru dikirim barengan ke web
    for instance_id in instances:
        try:
            response = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=['Average'],
                Unit='Percent'
            )

            datapoints = sorted(response.get('Datapoints', []), key=lambda x: x['Timestamp'])

            chart_data[instance_id] = {
                'labels': [dt['Timestamp'].strftime('%H:%M') for dt in datapoints],
                'data': [round(dt['Average'], 2) for dt in datapoints]
            }
        except Exception as e:
            print(f"Error metrik {instance_id}: {e}")

    return jsonify(chart_data)


# MULAI STRESS TEST (100% CPU)
@app.route("/trigger-stress", methods=["POST"])
def trigger_stress():
    instances = get_active_instances()
    if not instances:
        flash("Gagal: Tidak ada instance aktif yang ditemukan di ASG!")
        return redirect(url_for("index"))
    try:
        # Menembak perintah kompresi matematika berat ke semua server anak sekaligus
        # Dieksekusi 2 baris agar kedua core vCPU t3.micro langsung mentok 100%
        response = ssm_client.send_command(
            InstanceIds=instances,
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": [
                    "dd if=/dev/zero bs=100M count=500 | gzip | gzip -d > /dev/null &",
                    "dd if=/dev/zero bs=100M count=500 | gzip | gzip -d > /dev/null &"
                ]
            },
        )
        cmd_id = response["Command"]["CommandId"]
        flash(
            f"Perintah Stress Test ala AWS Academy dikirim ke SEMUA server ({len(instances)} instance). "
            f"CPU didorong ke maksimum! ID Perintah: {cmd_id}."
        )
    except Exception as e:
        flash(f"Error AWS SSM: {str(e)}")
    return redirect(url_for("index"))


# HENTIKAN STRESS TEST
@app.route("/stop-stress", methods=["POST"])
def stop_stress():
    instances = get_active_instances()
    if not instances:
        flash("Gagal: Tidak ada instance aktif!")
        return redirect(url_for("index"))
    try:
        # Menghentikan paksa semua proses gzip yang berjalan di latar belakang
        ssm_client.send_command(
            InstanceIds=instances,
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": ["sudo pkill gzip || true"]}
        )
        flash("Sukses! Perintah untuk menghentikan Stress Test (pkill gzip) telah dikirim ke semua server.")
    except Exception as e:
        flash(f"Gagal menyetop: {str(e)}")

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
