# your_app/management/commands/check_finished_estimates.py
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from dispatch.models import Estimate

class Command(BaseCommand):
    help = "Check and update is_finished for estimates"

    def handle(self, *args, **kwargs):
        self.stdout.write("Checking for finished estimates...")

        # '예약 완료' 상태이고 완료되지 않은 견적 가져오기
        estimates = Estimate.objects.filter(is_finished=False, status="예약 완료")
        updated_count = 0

        for estimate in estimates:
            # return_date의 날짜와 now의 날짜 비교
            if estimate.return_date and estimate.return_date.date() < now().date():
                estimate.is_finished = True
                estimate.finished_date = estimate.return_date.date()
                estimate.save()
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"{updated_count} estimates updated as finished."))
