#!/usr/bin/env python
"""
Check existing AWS resources for Plantcon
"""
import os
import subprocess
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

def run_aws_command(cmd, description):
    """Run AWS CLI command and return result"""
    try:
        print(f"🔍 {description}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"❌ 錯誤: {result.stderr}")
            return None
    except subprocess.TimeoutExpired:
        print(f"❌ 命令超時: {cmd}")
        return None
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
        return None

def main():
    print("🔍 檢查AWS資源狀態")
    print("=" * 50)
    
    # Check AWS credentials
    region = os.getenv('AWS_REGION', 'ap-southeast-2')
    
    # Set AWS environment variables
    os.environ['AWS_REGION'] = region
    os.environ['AWS_DEFAULT_REGION'] = region
    
    if os.getenv('AWS_ACCESS_KEY_ID'):
        os.environ['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID')
    if os.getenv('AWS_SECRET_ACCESS_KEY'):  
        os.environ['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    print(f"🌏 檢查區域: {region}")
    
    # Check identity
    identity = run_aws_command("aws sts get-caller-identity", "檢查AWS身份")
    if identity:
        try:
            identity_data = json.loads(identity)
            print(f"✅ AWS用戶: {identity_data.get('Arn', 'Unknown')}")
        except:
            print("⚠️ 無法解析身份資訊")
    else:
        print("❌ AWS憑證無效或已過期")
        print("\n📋 可能的解決方案:")
        print("1. 運行 'aws configure' 設置新的憑證")
        print("2. 檢查IAM用戶的訪問金鑰")
        print("3. 確認臨時憑證是否仍然有效")
        return
    
    print("\n🔍 檢查現有資源...")
    
    # Check Load Balancers
    print("\n1. 應用程式負載均衡器 (ALB):")
    albs = run_aws_command(f"aws elbv2 describe-load-balancers --region {region}", "查找ALB")
    if albs:
        try:
            alb_data = json.loads(albs)
            load_balancers = alb_data.get('LoadBalancers', [])
            
            if load_balancers:
                for lb in load_balancers:
                    name = lb.get('LoadBalancerName', 'Unknown')
                    dns_name = lb.get('DNSName', 'Unknown')
                    state = lb.get('State', {}).get('Code', 'Unknown')
                    scheme = lb.get('Scheme', 'Unknown')
                    
                    print(f"   📡 {name}")
                    print(f"      網址: http://{dns_name}")
                    print(f"      狀態: {state}")
                    print(f"      類型: {scheme}")
                    
                    if 'plantcon' in name.lower() or any('plantcon' in tag.get('Value', '').lower() for tag in lb.get('Tags', [])):
                        print(f"      🎯 這可能是你的Plantcon應用程式!")
                        print(f"      🌐 訪問網址: http://{dns_name}")
            else:
                print("   ❌ 沒有找到ALB")
        except Exception as e:
            print(f"   ❌ 解析ALB數據失敗: {e}")
    
    # Check ECS Services
    print("\n2. ECS服務:")
    clusters = run_aws_command(f"aws ecs list-clusters --region {region}", "查找ECS叢集")
    if clusters:
        try:
            cluster_data = json.loads(clusters)
            cluster_arns = cluster_data.get('clusterArns', [])
            
            if cluster_arns:
                for cluster_arn in cluster_arns:
                    cluster_name = cluster_arn.split('/')[-1]
                    print(f"   🏗️ 叢集: {cluster_name}")
                    
                    # Check services in cluster
                    services = run_aws_command(f"aws ecs list-services --cluster {cluster_name} --region {region}", f"查找 {cluster_name} 中的服務")
                    if services:
                        try:
                            service_data = json.loads(services)
                            service_arns = service_data.get('serviceArns', [])
                            
                            if service_arns:
                                for service_arn in service_arns:
                                    service_name = service_arn.split('/')[-1]
                                    print(f"      🔧 服務: {service_name}")
                                    
                                    # Get service details
                                    service_detail = run_aws_command(f"aws ecs describe-services --cluster {cluster_name} --services {service_name} --region {region}", f"獲取 {service_name} 詳情")
                                    if service_detail:
                                        try:
                                            detail_data = json.loads(service_detail)
                                            service_info = detail_data.get('services', [{}])[0]
                                            running_count = service_info.get('runningCount', 0)
                                            desired_count = service_info.get('desiredCount', 0)
                                            status = service_info.get('status', 'Unknown')
                                            
                                            print(f"         狀態: {status}")
                                            print(f"         運行中: {running_count}/{desired_count}")
                                        except:
                                            print(f"         ⚠️ 無法獲取詳細狀態")
                            else:
                                print(f"      ❌ {cluster_name} 中沒有服務")
                        except:
                            print(f"      ❌ 無法解析 {cluster_name} 的服務")
            else:
                print("   ❌ 沒有找到ECS叢集")
        except Exception as e:
            print(f"   ❌ 解析ECS數據失敗: {e}")
    
    # Check EC2 instances
    print("\n3. EC2實例:")
    instances = run_aws_command(f"aws ec2 describe-instances --region {region}", "查找EC2實例")
    if instances:
        try:
            instance_data = json.loads(instances)
            reservations = instance_data.get('Reservations', [])
            
            running_instances = []
            for reservation in reservations:
                for instance in reservation.get('Instances', []):
                    state = instance.get('State', {}).get('Name', 'Unknown')
                    if state == 'running':
                        instance_id = instance.get('InstanceId', 'Unknown')
                        public_ip = instance.get('PublicIpAddress', 'No public IP')
                        public_dns = instance.get('PublicDnsName', 'No public DNS')
                        instance_type = instance.get('InstanceType', 'Unknown')
                        
                        # Check tags for plantcon
                        tags = instance.get('Tags', [])
                        name_tag = next((tag['Value'] for tag in tags if tag['Key'] == 'Name'), 'No name')
                        
                        running_instances.append({
                            'id': instance_id,
                            'name': name_tag,
                            'type': instance_type,
                            'public_ip': public_ip,
                            'public_dns': public_dns
                        })
            
            if running_instances:
                for instance in running_instances:
                    print(f"   🖥️ {instance['name']} ({instance['id']})")
                    print(f"      類型: {instance['type']}")
                    if instance['public_ip'] != 'No public IP':
                        print(f"      🌐 公共IP: http://{instance['public_ip']}:8000")
                    if instance['public_dns'] != 'No public DNS':
                        print(f"      🌐 公共DNS: http://{instance['public_dns']}:8000")
                    
                    if 'plantcon' in instance['name'].lower():
                        print(f"      🎯 這可能是你的Plantcon應用程式!")
            else:
                print("   ❌ 沒有運行中的EC2實例")
        except Exception as e:
            print(f"   ❌ 解析EC2數據失敗: {e}")
    
    # Check RDS
    print("\n4. RDS資料庫:")
    rds_hostname = os.getenv('RDS_HOSTNAME')
    if rds_hostname:
        print(f"   ✅ 配置的RDS: {rds_hostname}")
        print(f"   🔐 已連接並設置完成")
    else:
        print("   ❌ 沒有配置RDS")
    
    print("\n" + "=" * 50)
    print("📋 總結:")
    print("=" * 50)
    
    print("\n🔍 如果找到了負載均衡器或EC2實例：")
    print("1. 點擊上面顯示的網址訪問你的應用程式")
    print("2. 使用 admin / plantcon123 登入")
    
    print("\n⚠️ 如果沒有找到運行中的服務：")
    print("1. 你的AWS基礎設施可能還沒有部署")
    print("2. 可能需要先建立ECS服務或EC2實例")
    print("3. 或者服務在不同的區域")
    
    print("\n🚀 下一步選項：")
    print("1. 如果有運行的服務 → 直接訪問網址")
    print("2. 如果沒有服務 → 需要部署基礎設施")
    print("3. 本地測試 → python test_app.py")

if __name__ == "__main__":
    main()