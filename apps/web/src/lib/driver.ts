interface DriverIdentity {
  first_name?: string | null;
  last_name?: string | null;
  full_name?: string | null;
  broadcast_name?: string | null;
  name_acronym?: string | null;
}

export function getDriverNameParts(driver: DriverIdentity): {
  firstName: string;
  lastName: string;
} {
  const firstName = driver.first_name?.trim();
  const lastName = driver.last_name?.trim();

  if (firstName || lastName) {
    return {
      firstName: firstName || driver.name_acronym || 'Driver',
      lastName: lastName || '',
    };
  }

  const fullName = driver.full_name?.trim() || driver.broadcast_name?.trim() || '';
  if (!fullName) {
    return {
      firstName: driver.name_acronym || 'Driver',
      lastName: '',
    };
  }

  const [firstToken, ...rest] = fullName.split(/\s+/);
  return {
    firstName: firstToken || driver.name_acronym || 'Driver',
    lastName: rest.join(' '),
  };
}

export function getDriverDisplayName(driver: DriverIdentity): string {
  const fullName = driver.full_name?.trim();
  if (fullName) {
    return fullName;
  }

  const { firstName, lastName } = getDriverNameParts(driver);
  return `${firstName} ${lastName}`.trim();
}
