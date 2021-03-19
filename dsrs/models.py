from django.db import models


class Territory(models.Model):
    name = models.CharField(max_length=48)
    code_2 = models.CharField(max_length=2)
    code_3 = models.CharField(max_length=3)
    local_currency = models.ForeignKey(
        "Currency", related_name="territories", on_delete=models.CASCADE
    )

    class Meta:
        db_table = "territory"
        verbose_name = "territory"
        verbose_name_plural = "territories"
        ordering = ("name",)

    def __str__(self):
        return self.code_2


class Currency(models.Model):
    name = models.CharField(max_length=48)
    symbol = models.CharField(max_length=4)
    code = models.CharField(max_length=3)

    class Meta:
        db_table = "currency"
        verbose_name = "currency"
        verbose_name_plural = "currencies"

    def __str__(self):
        return self.code


class DSR(models.Model):
    class Meta:
        db_table = "dsr"

    STATUS_ALL = (
        ("failed", "FAILED"),
        ("ingested", "INGESTED"),
    )

    path = models.CharField(max_length=256)
    period_start = models.DateField(null=False)
    period_end = models.DateField(null=False)

    status = models.CharField(
        choices=STATUS_ALL, default=STATUS_ALL[0][0], max_length=48
    )

    territory = models.ForeignKey(
        Territory, related_name="dsrs", on_delete=models.CASCADE
    )
    currency = models.ForeignKey(
        Currency, related_name="dsrs", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.territory}, {self.period_start} to {self.period_end}"


class Resource(models.Model):
    dsp_id = models.CharField(max_length=32, primary_key=True)
    title = models.CharField(max_length=256, null=True)
    artists = models.CharField(
        max_length=256, null=True,
        help_text="Multivalue, pipe-separated list of artist names."
    )

    isrc = models.CharField(max_length=16, null=True)
    usages = models.IntegerField(null=True)
    revenue = models.FloatField(null=True)
    dsrs = models.ManyToManyField(
        DSR, help_text="List of DSRs on which the resource is reported."
    )
