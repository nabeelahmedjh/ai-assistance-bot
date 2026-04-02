from django.db import migrations, models
import django.db.models.deletion
import pgvector.django


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        pgvector.django.VectorExtension(),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('source_type', models.CharField(default='manual', max_length=64)),
                ('file_url', models.URLField(blank=True, default='')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('processed', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Chunk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('embedding', pgvector.django.VectorField(dimensions=384)),
                ('chunk_index', models.PositiveIntegerField()),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chunks', to='documents.document')),
            ],
            options={
                'ordering': ['document_id', 'chunk_index'],
                'unique_together': {('document', 'chunk_index')},
            },
        ),
    ]
