#!/usr/bin/env python3
"""
Edge TTS Service - Python 客户端示例
"""
import requests
import argparse
import sys


def text_to_speech(text, output_file="speech.mp3", **kwargs):
    """
    调用 TTS 服务生成语音

    Args:
        text: 要转换的文本
        output_file: 输出文件路径
        **kwargs: 其他参数 (voice, rate, pitch, volume)
    """
    url = "http://localhost:8000/tts"

    payload = {"text": text, **kwargs}

    try:
        print(f"🎙️ 正在生成语音...")
        print(f"   文本: {text[:50]}{'...' if len(text) > 50 else ''}")
        if kwargs.get("voice"):
            print(f"   音色: {kwargs['voice']}")

        response = requests.post(url, json=payload, timeout=30)

        if response.status_code == 200:
            with open(output_file, "wb") as f:
                f.write(response.content)
            print(f"✅ 语音已保存到: {output_file}")
            print(f"   文件大小: {len(response.content)} 字节")
            return True
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"   错误: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务，请确保服务已启动")
        print("   运行: bash scripts/start.sh")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False


def list_voices(locale=None):
    """获取可用音色列表"""
    url = "http://localhost:8000/voices"
    if locale:
        url += f"?locale={locale}"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"🎭 可用音色 (共 {data['total']} 个):")
            print()
            for voice in data['voices'][:10]:  # 只显示前 10 个
                print(f"  - {voice['id']}")
                print(f"    语言: {voice['locale_name']} ({voice['locale']})")
                print(f"    性别: {voice['gender']}")
                if voice.get('description'):
                    print(f"    描述: {voice['description']}")
                print()
            return True
        else:
            print(f"❌ 获取音色列表失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Edge TTS Service 客户端")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # TTS 命令
    tts_parser = subparsers.add_parser("tts", help="文本转语音")
    tts_parser.add_argument("text", help="要转换的文本")
    tts_parser.add_argument("-o", "--output", default="speech.mp3", help="输出文件路径")
    tts_parser.add_argument("-v", "--voice", help="音色 ID 或简称 (如: xiaoxiao)")
    tts_parser.add_argument("--rate", default="+0%", help="语速 (如: +10%, -20%)")
    tts_parser.add_argument("--pitch", default="+0Hz", help="音调 (如: +10Hz, -5Hz)")
    tts_parser.add_argument("--volume", default="+0%", help="音量 (如: +10%, -50%)")

    # 音色列表命令
    voices_parser = subparsers.add_parser("voices", help="获取音色列表")
    voices_parser.add_argument("-l", "--locale", help="筛选语言 (如: zh-CN, en-US)")

    # 测试命令
    test_parser = subparsers.add_parser("test", help="测试服务连接")

    args = parser.parse_args()

    if args.command == "tts":
        kwargs = {}
        if args.voice:
            kwargs["voice"] = args.voice
        if args.rate != "+0%":
            kwargs["rate"] = args.rate
        if args.pitch != "+0Hz":
            kwargs["pitch"] = args.pitch
        if args.volume != "+0%":
            kwargs["volume"] = args.volume

        text_to_speech(args.text, args.output, **kwargs)

    elif args.command == "voices":
        list_voices(args.locale)

    elif args.command == "test":
        import requests
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ 服务运行正常")
                print(response.json())
            else:
                print(f"❌ 服务异常: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ 无法连接到服务: {e}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
