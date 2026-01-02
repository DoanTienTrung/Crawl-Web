"""
News Scraper Scheduler
Tự động lập lịch chạy các scraper functions theo cấu hình trong scheduler_config.json

Usage:
    python scheduler.py
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# Import các scraper functions từ main.py
from main import (
    scrape_all,
    scrape_cafef,
    scrape_cafeland,
    scrape_vnexpress,
    scrape_vneconomy,
    scrape_vov,
    scrape_vietnamnet,
    scrape_dantri,
    scrape_thanhnien,
    scrape_tuoitre,
    scrape_laodong,
    scrape_nld,
    scrape_vietstock,
    scrape_antt,
    scrape_cna,
    scrape_qdnd,
    scrape_kinhte,
    scrape_thoibaonganhang,
    scrape_taichinhdoanhnghiep,
    scrape_baochinhphu,
    scrape_tinnhanhchungkhoan,
)


class NewsScraperScheduler:
    """
    Scheduler để tự động chạy các scraper functions theo lịch
    Cấu hình qua file JSON: scheduler_config.json
    """

    # Mapping function names trong config → actual Python functions
    SCRAPER_FUNCTIONS = {
        'scrape_all': scrape_all,
        'scrape_cafef': scrape_cafef,
        'scrape_cafeland': scrape_cafeland,
        'scrape_vnexpress': scrape_vnexpress,
        'scrape_vneconomy': scrape_vneconomy,
        'scrape_vov': scrape_vov,
        'scrape_vietnamnet': scrape_vietnamnet,
        'scrape_dantri': scrape_dantri,
        'scrape_thanhnien': scrape_thanhnien,
        'scrape_tuoitre': scrape_tuoitre,
        'scrape_laodong': scrape_laodong,
        'scrape_nld': scrape_nld,
        'scrape_vietstock': scrape_vietstock,
        'scrape_antt': scrape_antt,
        'scrape_cna': scrape_cna,
        'scrape_qdnd': scrape_qdnd,
        'scrape_kinhte': scrape_kinhte,
        'scrape_thoibaonganhang': scrape_thoibaonganhang,
        'scrape_taichinhdoanhnghiep': scrape_taichinhdoanhnghiep,
        'scrape_baochinhphu': scrape_baochinhphu,
        'scrape_tinnhanhchungkhoan': scrape_tinnhanhchungkhoan,
    }

    def __init__(self, config_file='scheduler_config.json'):
        """
        Khởi tạo scheduler

        Args:
            config_file: Đường dẫn đến file JSON config
        """
        self.config_file = config_file
        self.config = None
        self.scheduler = None
        self.logger = None

        # Load config và setup
        self.load_config()
        self.setup_logging()
        self.setup_scheduler()

    def load_config(self):
        """Đọc file JSON config"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"✓ Loaded config from: {self.config_file}")
        except FileNotFoundError:
            print(f"❌ Config file not found: {self.config_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in config file: {e}")
            sys.exit(1)

    def setup_logging(self):
        """Setup logging system với file rotation"""
        log_file = self.config.get('log_file', 'logs/news_scheduler.log')
        log_level = self.config.get('log_level', 'INFO')

        # Tạo logs folder nếu chưa có
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Setup rotating file handler (max 10MB, keep 5 files)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )

        # Formatter
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        # Setup logger
        self.logger = logging.getLogger('NewsScheduler')
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        self.logger.addHandler(file_handler)

        # Console handler cho debugging
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        self.logger.info("=" * 60)
        self.logger.info("📰 News Scraper Scheduler Initialized")
        self.logger.info("=" * 60)

    def setup_scheduler(self):
        """Khởi tạo APScheduler"""
        timezone = self.config.get('timezone', 'Asia/Ho_Chi_Minh')
        self.scheduler = BackgroundScheduler(timezone=timezone)
        self.logger.info(f"⏰ Timezone: {timezone}")

    def get_function_by_name(self, func_name):
        """
        Map function name string → actual Python function

        Args:
            func_name: Tên function (vd: "scrape_cafef")

        Returns:
            Function object hoặc None nếu không tìm thấy
        """
        return self.SCRAPER_FUNCTIONS.get(func_name)

    def create_trigger(self, schedule_config):
        """
        Tạo trigger cho job từ schedule config

        Args:
            schedule_config: Dict chứa schedule info từ JSON

        Returns:
            IntervalTrigger hoặc CronTrigger
        """
        schedule_type = schedule_config.get('type')

        if schedule_type == 'interval':
            # Interval trigger: mỗi X giây/phút/giờ/ngày
            kwargs = {}
            if 'seconds' in schedule_config:
                kwargs['seconds'] = schedule_config['seconds']
            if 'minutes' in schedule_config:
                kwargs['minutes'] = schedule_config['minutes']
            if 'hours' in schedule_config:
                kwargs['hours'] = schedule_config['hours']
            if 'days' in schedule_config:
                kwargs['days'] = schedule_config['days']

            return IntervalTrigger(**kwargs)

        elif schedule_type == 'cron':
            # Cron trigger: theo lịch cụ thể
            kwargs = {}
            if 'minute' in schedule_config:
                kwargs['minute'] = schedule_config['minute']
            if 'hour' in schedule_config:
                kwargs['hour'] = schedule_config['hour']
            if 'day' in schedule_config:
                kwargs['day'] = schedule_config['day']
            if 'month' in schedule_config:
                kwargs['month'] = schedule_config['month']
            if 'day_of_week' in schedule_config:
                kwargs['day_of_week'] = schedule_config['day_of_week']

            return CronTrigger(**kwargs)

        else:
            raise ValueError(f"Unknown schedule type: {schedule_type}")

    def run_job_wrapper(self, job_function, job_name, job_id):
        """
        Wrapper để chạy job với logging và error handling

        Args:
            job_function: Function cần chạy
            job_name: Tên job (để log)
            job_id: ID của job
        """
        self.logger.info("=" * 60)
        self.logger.info(f"▶️  Starting job: {job_name} (ID: {job_id})")
        start_time = datetime.now()

        try:
            # Chạy scraper function
            # Các hàm trong main.py mặc định đã có save_to_db=True, export_csv=True
            result = job_function()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            # Đếm số articles
            article_count = len(result) if result else 0

            self.logger.info(
                f"✅ Completed job: {job_name} | "
                f"Articles: {article_count} | "
                f"Duration: {duration:.2f}s"
            )

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.logger.error(
                f"❌ Failed job: {job_name} | "
                f"Error: {str(e)} | "
                f"Duration: {duration:.2f}s",
                exc_info=True
            )
            # Không raise exception để scheduler tiếp tục chạy jobs khác

        finally:
            self.logger.info("=" * 60)

    def add_jobs_from_config(self):
        """Thêm các jobs từ config vào scheduler"""
        jobs = self.config.get('jobs', [])

        if not jobs:
            self.logger.warning("⚠️  No jobs found in config!")
            return

        enabled_count = 0
        disabled_count = 0

        for job_config in jobs:
            job_id = job_config.get('id')
            job_name = job_config.get('name', job_id)
            func_name = job_config.get('function')
            enabled = job_config.get('enabled', True)
            schedule_config = job_config.get('schedule')
            description = job_config.get('description', '')

            # Skip nếu job bị disable
            if not enabled:
                self.logger.info(f"⏭️  Skipped (disabled): {job_name}")
                disabled_count += 1
                continue

            # Lấy function
            job_function = self.get_function_by_name(func_name)
            if not job_function:
                self.logger.error(f"❌ Unknown function: {func_name} for job {job_id}")
                continue

            # Tạo trigger
            try:
                trigger = self.create_trigger(schedule_config)
            except Exception as e:
                self.logger.error(f"❌ Invalid schedule for job {job_id}: {e}")
                continue

            # Thêm job vào scheduler
            self.scheduler.add_job(
                func=self.run_job_wrapper,
                trigger=trigger,
                args=[job_function, job_name, job_id],
                id=job_id,
                name=job_name,
                replace_existing=True
            )

            self.logger.info(f"✓ Added job: {job_name} - {description}")
            enabled_count += 1

        self.logger.info(f"\n📋 Summary: {enabled_count} jobs enabled, {disabled_count} jobs disabled")

    def start(self):
        """Start scheduler"""
        try:
            # Thêm jobs từ config
            self.add_jobs_from_config()

            # Start scheduler
            self.scheduler.start()

            self.logger.info("\n🚀 Scheduler started successfully!")
            self.logger.info(f"⏰ Timezone: {self.config.get('timezone')}")
            self.logger.info(f"📋 Total active jobs: {len(self.scheduler.get_jobs())}\n")

            # In danh sách jobs và thời gian chạy tiếp theo
            for job in self.scheduler.get_jobs():
                next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'N/A'
                self.logger.info(f"  🕐 {job.name}")
                self.logger.info(f"     Next run: {next_run}")

            self.logger.info("\n" + "=" * 60)
            self.logger.info("Press Ctrl+C to stop scheduler")
            self.logger.info("=" * 60 + "\n")

            # Chạy ngay 1 lần nếu config yêu cầu
            if self.config.get('run_on_startup', False):
                self.logger.info("🔄 Running all enabled jobs on startup...")
                for job in self.scheduler.get_jobs():
                    job.func(*job.args)

            # Keep running (blocking)
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()

        except Exception as e:
            self.logger.error(f"❌ Scheduler failed to start: {e}", exc_info=True)
            raise

    def stop(self):
        """Graceful shutdown"""
        self.logger.info("\n⏸️  Shutting down scheduler...")
        self.logger.info("⏳ Waiting for running jobs to complete...")

        self.scheduler.shutdown(wait=True)

        self.logger.info("✅ Scheduler stopped gracefully")
        self.logger.info("=" * 60)


def main():
    """Main entry point"""
    print("\n" + "=" * 60)
    print("📰 News Scraper Scheduler")
    print("=" * 60 + "\n")

    # Tạo scheduler instance
    scheduler = NewsScraperScheduler()

    # Start scheduler (blocking)
    scheduler.start()


if __name__ == "__main__":
    main()
