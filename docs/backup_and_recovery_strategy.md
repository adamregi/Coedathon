# Enterprise Backup and Disaster Recovery Strategy

This document outlines the operational backup policy, encryption standards, point-in-time recovery (PITR) mechanism, automated drills, and recovery runbook for the backend database infrastructure.

---

## 1. Backup Tiers & Cadence

| Tier | Type | Frequency | Retention Window | Storage Target |
|---|---|---|---|---|
| **Tier 1 (Continuous)** | MySQL Binary Logs (Binlogs) | Continuous streaming | 7 Days | Geo-replicated Encrypted S3 / GCS |
| **Tier 2 (Daily Snapshot)** | Logical / Physical Snapshot (`mysqldump` / `Percona XtraBackup`) | Every 24 hours (02:00 UTC) | 30 Days | Geo-replicated Encrypted S3 Bucket |
| **Tier 3 (Weekly Archive)** | Full System Archive (schema + data + audit logs) | Weekly (Sunday 03:00 UTC) | 90 Days | Infrequent Access Storage |
| **Tier 4 (Yearly Compliance)** | Immutable Write-Once-Read-Many (WORM) Archive | Annually | 7 Years | AWS S3 Glacier Vault / GCS Archive |

---

## 2. Encryption and Security Architecture

1. **Encryption-in-Transit**: All backup replication streams and database connections enforce TLS 1.3 with forward secrecy.
2. **Encryption-at-Rest**:
   - Backup files are encrypted before leaving the database host using AES-256-GCM.
   - Master encryption keys are managed through AWS KMS / GCP Cloud KMS with annual automatic key rotation.
   - Access to KMS decryption keys requires multi-factor authentication (MFA) and is governed by strict IAM policies.
3. **Immutability & Object Locking**:
   - Backup storage buckets utilize Object Lock in compliance mode to prevent accidental deletion, ransomware tampering, or unauthorized modification.

---

## 3. Point-in-Time Recovery (PITR)

- **Target RPO (Recovery Point Objective)**: < 5 minutes.
- **Target RTO (Recovery Time Objective)**: < 30 minutes.
- **Mechanism**:
  1. Restore the latest daily full snapshot prior to the incident timestamp.
  2. Replay streamed binary logs sequentially up to the specific target timestamp (or GTID):
     ```bash
     mysqlbinlog --read-from-remote-server \
                 --host=backup-vault.internal \
                 --start-datetime="2026-09-05 02:00:00" \
                 --stop-datetime="2026-09-05 11:15:00" \
                 binlog.000142 | mysql -u root -p
     ```

---

## 4. Automated Restoration Testing Drills

- **Weekly Automated Test Drill**:
  - An isolated ephemeral environment is automatically spawned via CI/CD every Wednesday.
  - The latest snapshot is decrypted, imported, and integrity verified.
  - Smoke tests and consistency checks (`SELECT COUNT(*)` on users, applications, and analysis runs) run automatically.
  - A notification is sent to the DevOps Slack/PagerDuty channel confirming restoration health and duration.
- **Quarterly Disaster Recovery Simulation**:
  - Simulated failover to secondary cloud region.
  - Audit logging of recovery performance against SLA targets.

---

## 5. Recovery Runbook (Step-by-Step)

### Step 1: Incident Declaration & Triage
1. Identify the root cause (hardware failure, data corruption, unauthorized data deletion).
2. Freeze writes to the live database (set `READ_ONLY=ON`).
3. Determine target recovery timestamp ($T_{target}$).

### Step 2: Provision Isolated Recovery Instance
1. Launch clean MySQL instance in a secure VPC.
2. Ensure network security rules prevent public ingress.

### Step 3: Fetch & Decrypt Snapshot
```bash
aws s3 cp s3://codethon-db-backups/daily/2026-09-05-full.xbstream.enc ./
gpg --decrypt --recipient ops-key@company.com 2026-09-05-full.xbstream.enc > snapshot.xbstream
mbstream -x < snapshot.xbstream -C /var/lib/mysql-recovery
```

### Step 4: Prepare & Apply Binlogs
```bash
xtrabackup --prepare --target-dir=/var/lib/mysql-recovery
chown -R mysql:mysql /var/lib/mysql-recovery
systemctl start mysql-recovery
mysqlbinlog --stop-datetime="$T_TARGET" /var/log/mysql/binlog.* | mysql -u root -p
```

### Step 5: Verification & Traffic Cutover
1. Execute application consistency validation script:
   `python scripts/verify_db_integrity.py`
2. Update backend database connection string in Secret Manager.
3. Restart backend service pods.
4. Verify `/health` probe returns `200 OK`.
