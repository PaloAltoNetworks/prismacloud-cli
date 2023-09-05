# How to enable or disable policies at scale via CSV

## 📋 Description

- Added `--csv` option to the `policy set` command.
- Enable or disable policies at scale using a CSV file.

## 🎯 Motivation and Context

- Update out-of-the-box policy statuses using a CSV.
- Flexibility to only update specific policies.

## 📝 How to Use

1️⃣ **Generate Example CSV:**  
```bash
pc -o csv --columns policyId,enabled,^name$ policy list|head -n 5 > ~/policies.csv
```

2️⃣ **Edit the CSV:**  
```csv
policyId,name,enabled
82908c8a-6bb8-4c63-b4b5-24967c9f7145,S3 bucket MFA Delete is not enabled,True
...
```

3️⃣ **Run Command:**  
```bash
python3 bin/pc -v policy set --csv ~/policies.csv
```

## 🧪 How Has This Been Tested?

- Dry-run option available: `--dry-run`
```bash
python3 bin/pc -v policy set --csv ~/policies.csv --dry-run
```

## 📸 Screenshots

![Overview](https://github.com/PaloAltoNetworks/prismacloud-cli/assets/96180461/eb6af137-37a7-4d32-9773-8319d78a81ef)
